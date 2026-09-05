"""Unit tests for the site's arithmetic, on synthetic notices.

These build a database the same way a real run does - through
Store.diff_and_update_messages - so open/closed and the horizon come from the
collector's own semantics rather than from a hand-made fixture.
"""

from __future__ import annotations

import itertools
import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from lift_site import model, render
from lift_status.store import DEFAULT_GRACE_MISSES, Store
from tests.helpers import make_item

_run_counter = itertools.count()

# A synthetic collection that starts where the real one did.
T0 = model.COLLECTION_START
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=UTC)


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def lift(station="Athy", code="ATHY", planned=False, start="2026-08-01T09:00:00", **over):
    text = (
        "The lift at platform 1 is temporarily unavailable due to planned works."
        if planned
        else "The lift at platform 1 is currently out of service."
    )
    item = make_item(
        head=f"{station} - Lift out of order",
        text=text,
        start=start,
        codes=[code],
        event_stops=[{"sStop": station, "eStop": station, "direction": "1"}],
    )
    item.update(over)
    return item


def escalator(station="Dublin Connolly", code="CNLLY", **over):
    return lift(
        station=station,
        code=code,
        head=f"{station.split(' ')[-1]} - Escalator out of order",
        text="The Escalator at the main concourse is currently out of service.",
        **over,
    )


class SiteModelCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.store = Store(self.dir)
        os.environ.pop("LIFT_STATUS_GRACE_MISSES", None)
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(self.store.conn.close)

    def poll(self, at, items):
        """One successful run: what the feed showed at `at`."""
        run_id = self.store.begin_run_success(f"run-{next(_run_counter)}", iso(at), 200)
        self.store.diff_and_update_messages(run_id, iso(at), items)
        self.store.finalize_run(run_id, iso(at), len(items), 0, 0)

    def drop(self, at, every=timedelta(minutes=30)):
        """Poll the notice away for good, starting at `at`.

        One empty poll no longer closes anything, but the outage still ends at
        `at`, the first poll it was absent from.
        """
        for i in range(DEFAULT_GRACE_MISSES):
            self.poll(at + i * every, [])

    def fail_run(self, at):
        self.store.record_run_failure(
            f"run-{next(_run_counter)}", iso(at), iso(at), "unreachable", None, "boom", 3
        )

    def load(self, now=NOW):
        self.store.conn.commit()
        outages, until = model.load_outages(self.dir / "lift_status.db", now)
        self.until = until
        return outages


class TestClassification(unittest.TestCase):
    def test_lift_notices_in_every_wording_seen_live(self):
        for head in (
            "Rush and Lusk - Lift out of order",
            "Skerries - Lifts out of order",
            "Thurles - Lift out of service",
        ):
            self.assertEqual(model.classify(head), "lift", head)

    def test_escalators_are_their_own_kind(self):
        self.assertEqual(model.classify("Connolly - Escalator out of order"), "escalator")

    def test_the_rest_of_the_feed_is_not_this_sites_subject(self):
        for head in (
            "Service delay +25",
            "Station currently closed",
            "Customer Notice: This train has reduced capacity",
            "Services Suspended due to a vehicle striking Serpentine Level Crossing",
            "",
            None,
        ):
            self.assertIsNone(model.classify(head), head)

    def test_planned_works_is_what_the_notice_says(self):
        self.assertTrue(model.is_planned("temporarily unavailable due to planned works."))
        self.assertFalse(model.is_planned("The lift is currently out of service."))
        self.assertFalse(model.is_planned(None))


class TestStation(SiteModelCase):
    def test_name_comes_from_the_stop_and_identity_from_the_code(self):
        self.poll(T0, [escalator()])
        (o,) = self.load()
        self.assertEqual((o.code, o.station), ("CNLLY", "Dublin Connolly"))

    def test_the_head_is_the_fallback_when_a_notice_has_no_stops(self):
        item = lift(station="Athy")
        item["eventStops"] = []
        self.poll(T0, [item])
        (o,) = self.load()
        self.assertEqual(o.station, "Athy")

    def test_the_index_uses_the_newest_name_and_sorts_by_it(self):
        self.poll(T0, [lift(station="Athy", code="ATHY"), lift(station="Bray", code="BRAY")])
        self.poll(T0 + timedelta(hours=1), [lift(station="Athy Station", code="ATHY")])
        outages = self.load()
        self.assertEqual(model.station_index(outages), {"ATHY": "Athy Station", "BRAY": "Bray"})


class TestListing(SiteModelCase):
    def test_an_outage_is_listed_from_first_sighting_to_first_absence(self):
        self.poll(T0, [lift()])
        self.poll(T0 + timedelta(minutes=30), [lift()])
        gone = T0 + timedelta(minutes=60)
        self.drop(gone)
        (o,) = self.load()
        self.assertEqual((o.first_seen, o.end, o.ongoing), (T0, gone, False))
        self.assertEqual(o.kind, "lift")
        self.assertFalse(o.planned)

    def test_irish_rails_start_is_kept_but_is_not_the_listing(self):
        # Ballybrophy: "since 5 May", first listed 13 August. The claim is
        # carried on the outage; the interval measured is the listing.
        self.poll(T0, [])
        seen = T0 + timedelta(days=5)
        self.poll(seen, [lift(start="2026-05-05T00:00:00")])
        (o,) = self.load()
        self.assertEqual(o.start, datetime(2026, 5, 4, 23, 0, tzinfo=UTC))
        self.assertEqual(o.first_seen, seen)

    def test_a_notice_still_up_ends_at_the_horizon_not_the_clock(self):
        last = T0 + timedelta(hours=3)
        self.poll(T0, [lift()])
        self.poll(last, [lift()])
        (o,) = self.load(now=NOW)
        self.assertTrue(o.ongoing)
        self.assertEqual(o.end, last)
        self.assertEqual(self.until, last)

    def test_the_horizon_ignores_runs_that_never_reached_the_feed(self):
        self.poll(T0, [lift()])
        self.fail_run(T0 + timedelta(hours=1))
        self.load()
        self.assertEqual(self.until, T0)

    def test_planned_and_escalator_flags(self):
        self.poll(T0, [lift(planned=True), escalator()])
        by_kind = {o.kind: o for o in self.load()}
        self.assertTrue(by_kind["lift"].planned)
        self.assertFalse(by_kind["escalator"].planned)


class TestMergeEdits(SiteModelCase):
    def test_a_notice_reissued_in_the_same_poll_is_one_outage(self):
        # The head is part of the collector's identity key, so a reworded
        # head is a new message to it: the old one closes at the poll the new
        # one appears. To a reader it is the same lift.
        self.poll(T0, [lift()])
        edit = T0 + timedelta(minutes=30)
        reissued = lift(head="Athy - Lifts out of order",
                        text="The lifts at platforms 1 and 2 are currently out of service.")
        self.poll(edit, [reissued])
        self.poll(edit + timedelta(minutes=30), [reissued])
        (o,) = self.load()
        self.assertTrue(o.ongoing)
        self.assertEqual(o.first_seen, T0)
        self.assertIn("platforms 1 and 2", o.text)
        self.assertEqual(len(o.updates), 1)
        self.assertEqual(o.updates[0][0], edit)

    def test_a_reissue_takes_the_earliest_start_and_the_newest_works_flag(self):
        # A corrected start changes the identity key too. The replaced notice
        # is only a miss at the reissuing poll, so the merge takes one more.
        reissued = lift(start="2026-08-01T09:00:00", planned=True)
        self.poll(T0, [lift(start="2026-08-05T09:00:00")])
        self.poll(T0 + timedelta(minutes=30), [reissued])
        self.poll(T0 + timedelta(minutes=60), [reissued])
        (o,) = self.load()
        self.assertEqual(o.start, datetime(2026, 8, 1, 8, 0, tzinfo=UTC))
        self.assertTrue(o.planned)

    def test_a_notice_that_comes_back_a_poll_later_is_a_separate_outage(self):
        self.poll(T0, [lift()])
        self.drop(T0 + timedelta(minutes=30))
        self.poll(T0 + timedelta(days=1), [lift(start="2026-08-09T09:00:00")])
        outages = self.load()
        self.assertEqual(len(outages), 2)
        self.assertEqual([o.ongoing for o in outages], [True, False])  # newest first

    def test_the_same_notice_coming_back_is_two_outages_with_the_gap_intact(self):
        """The identity key is unchanged, so the collector reopens one row.

        The reopen test alongside gives the returning notice a corrected
        start, which makes it a new row instead, so nothing covered this.
        """
        self.poll(T0, [lift()])
        self.drop(T0 + timedelta(minutes=30))
        back = T0 + timedelta(days=14)
        self.poll(back, [lift()])
        outages = self.load()
        self.assertEqual(len(outages), 2)
        newest, oldest = outages
        self.assertEqual(oldest.first_seen, T0)
        self.assertEqual(oldest.end, T0 + timedelta(minutes=30))
        self.assertFalse(oldest.ongoing)
        self.assertEqual(newest.first_seen, back)
        self.assertTrue(newest.ongoing)

    def test_a_gap_splits_the_listing_without_refreshing_the_works_grace(self):
        """Works that blink off the feed are still works that ran for a month."""
        self.poll(T0, [lift(planned=True)])
        for day in range(1, 10):
            self.poll(T0 + timedelta(days=day), [lift(planned=True)])
        self.drop(T0 + timedelta(days=10))
        self.poll(T0 + timedelta(days=10, hours=1), [lift(planned=True)])
        outages = self.load()
        self.assertEqual(len(outages), 2)
        # The short second stretch would sit inside the grace on its own.
        self.assertLess(outages[0].end - outages[0].first_seen, model.PLANNED_GRACE)
        for o in outages:
            self.assertGreater(o.planned_total, model.PLANNED_GRACE)
            self.assertTrue(all(counts for _, _, counts in model.day_marks(o, T0, NOW)))

    def test_a_notice_reissued_and_reverted_counts_its_works_once(self):
        """A chain can hold two spans of one notice, and the grace is pooled
        per notice, so summing per span counted the reverted one twice."""
        works = lift(planned=True)
        reissued = lift(planned=True, head="Athy - Lifts out of order")
        for i in range(4):
            self.poll(T0 + timedelta(hours=12 * i), [works])
        for i in range(4, 8):
            self.poll(T0 + timedelta(hours=12 * i), [reissued])
        for i in range(8, 12):
            self.poll(T0 + timedelta(hours=12 * i), [works])
        (o,) = self.load(now=T0 + timedelta(days=7))
        self.assertEqual(len(o.segments), 3)
        self.assertEqual(o.planned_total, o.end - o.first_seen)
        self.assertLess(o.planned_total, model.PLANNED_GRACE)

    def test_a_reissue_merges_past_a_second_notice_still_up_at_the_station(self):
        # Two lifts listed at one station; one notice is reworded. The other,
        # still open, sorts between the closed notice and its replacement -
        # matching only against the newest chain would leave them unmerged.
        b = lift(text="The lift at platform 2 is currently out of service.")
        a = lift(
            text="The lift at platform 1 is currently out of service.", start="2026-08-02T09:00:00"
        )
        edit = T0 + timedelta(minutes=30)
        b2 = dict(b, head="Athy - Lifts out of order")
        self.poll(T0, [b, a])
        self.poll(edit, [a, b2])
        self.poll(edit + timedelta(minutes=30), [a, b2])
        outages = self.load()
        self.assertEqual(len(outages), 2)
        merged = [o for o in outages if o.updates]
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].first_seen, T0)
        self.assertEqual(merged[0].updates[0][0], edit)

    def test_two_notices_up_at_once_at_one_station_stay_two(self):
        a = lift(text="The lift at platform 1 is currently out of service.")
        b = lift(
            text="The lift at platform 2 is currently out of service.", start="2026-08-02T09:00:00"
        )
        self.poll(T0, [a])
        self.poll(T0 + timedelta(minutes=30), [a, b])
        self.poll(T0 + timedelta(minutes=60), [b])
        self.assertEqual(len(self.load()), 2)

    def test_a_lift_and_an_escalator_never_merge(self):
        self.poll(T0, [lift(station="Dublin Pearse", code="PERSE")])
        self.poll(T0 + timedelta(minutes=30), [escalator(station="Dublin Pearse", code="PERSE")])
        kinds = sorted(o.kind for o in self.load())
        self.assertEqual(kinds, ["escalator", "lift"])


class TestStationMonth(SiteModelCase):
    def cells(self, outages, ym="2026-08", now=NOW):
        return model.station_month(outages, ym, now, self.until)

    def test_cells_cover_the_month_and_mark_what_was_not_watched(self):
        self.poll(T0, [lift()])
        self.drop(T0 + timedelta(days=2))
        s = self.cells(self.load())
        self.assertEqual(len(s["cells"]), 31)
        # 1-7 August: before collection. 8-10: listed, the 10th only until the
        # horizon at 21:30. 11-20: no data (the 20th has begun by `now`, so it
        # is not "still to come"). 21 onwards is after `now`.
        self.assertEqual(s["cells"][:7], "8" * 7)
        self.assertEqual(s["cells"][7:10], "111")
        self.assertEqual(s["cells"][10:20], "8" * 10)
        self.assertEqual(s["cells"][20:], "9" * 11)
        self.assertEqual((s["faults"], s["planned"]), (1, 0))
        # three of the three days watched were listed
        self.assertEqual((s["observed"], s["against"], s["avail"]), (3, 3, 0))
        self.assertIsNone(s["esc_cells"])
        self.assertFalse(s["ongoing"])

    def test_days_before_collection_are_no_data_not_working_lifts(self):
        self.poll(T0, [lift(start="2025-05-14T09:00:00")])
        s = self.cells(self.load())
        self.assertEqual(s["cells"][:7], "8888888")

    def test_a_quiet_station_month_is_clear_inside_the_window_only(self):
        self.poll(T0, [])
        self.poll(T0 + timedelta(days=1), [])
        self.load()
        s = self.cells([])
        self.assertEqual(s["cells"], "8888888" + "00" + "8" * 11 + "9" * 11)
        self.assertEqual((s["observed"], s["against"], s["avail"], s["grade"]), (2, 0, 100, "A"))

    def test_a_fault_beats_planned_works_and_an_escalator_gets_its_own_bar(self):
        fault = lift(text="The lift is currently out of service.", start="2026-08-02T00:00:00")
        self.poll(T0, [lift(planned=True), escalator(), fault])
        self.poll(T0 + timedelta(hours=2), [lift(planned=True), escalator(), fault])
        outages = self.load()
        s = self.cells(outages)
        self.assertEqual(s["cells"][7], "1")
        # The escalator never paints the lift bar: it has one of its own.
        self.assertEqual(s["esc_cells"][7], "1")
        s = self.cells([o for o in outages if o.kind == "escalator" or o.planned])
        self.assertEqual((s["cells"][7], s["esc_cells"][7]), ("5", "1"))
        s = self.cells([o for o in outages if o.planned])
        self.assertEqual(s["cells"][7], "5")
        self.assertIsNone(s["esc_cells"])

    def test_an_escalator_notice_paints_its_own_bar_and_not_the_grade(self):
        # Pearse in August 2026 graded F on an escalator alone, beside a line
        # saying the outage did not remove step-free access (issue #32).
        self.poll(T0, [escalator(station="Dublin Pearse", code="PERSE")])
        self.poll(T0 + timedelta(days=2), [escalator(station="Dublin Pearse", code="PERSE")])
        s = self.cells(self.load())
        self.assertEqual(set(s["cells"]) - set("89"), {"0"})
        self.assertEqual(s["esc_cells"][7:10], "111")
        self.assertEqual((s["against"], s["avail"], s["grade"]), (0, 100, "A"))

    def test_a_lift_beside_an_escalator_counts_only_the_lifts_days(self):
        esc = escalator(station="Dublin Pearse", code="PERSE")
        self.poll(T0, [esc, lift(station="Dublin Pearse", code="PERSE")])
        self.poll(T0 + timedelta(minutes=30), [esc])
        self.poll(T0 + timedelta(hours=1), [esc])
        self.poll(T0 + timedelta(days=2), [esc])
        s = self.cells(self.load())
        self.assertEqual((s["cells"][7:10], s["esc_cells"][7:10]), ("100", "111"))
        self.assertEqual((s["observed"], s["against"], s["avail"], s["grade"]), (3, 1, 66, "E"))

    def test_planned_works_are_excused_for_a_week_and_not_a_day_longer(self):
        short = model.PLANNED_GRACE - timedelta(hours=1)
        self.poll(T0, [lift(planned=True)])
        self.poll(T0 + short, [lift(planned=True)])
        self.drop(T0 + short + timedelta(minutes=30))
        s = self.cells(self.load())
        self.assertEqual(s["cells"][7:15], "5" * 8)
        self.assertEqual((s["against"], s["avail"], s["grade"]), (0, 100, "A"))

        self.setUp()
        long = model.PLANNED_GRACE + timedelta(hours=1)
        self.poll(T0, [lift(planned=True)])
        self.poll(T0 + long, [lift(planned=True)])
        self.drop(T0 + long + timedelta(minutes=30))
        s = self.cells(self.load())
        # an hour past the grace and every day of it counts, the first week
        # included; the closing poll falls after Dublin midnight, so nine days
        # carry the notice rather than the short run's eight
        # ... and they change colour with it: one blue for works that count and
        # works that do not said opposite things in the same shade.
        self.assertEqual(s["cells"][7:16], "6" * 9)
        self.assertEqual((s["against"], s["avail"], s["grade"]), (9, 0, "F"))

    def test_a_day_carries_the_worst_of_what_was_listed_on_it(self):
        """Three shades can share a day now, so the ranking is explicit.

        A fault outranks works that outran their grace, which outrank works
        still inside it - and the arithmetic behind the last pair is opposite,
        so drawing them alike is what the second planned colour exists to stop.
        """
        long = model.PLANNED_GRACE + timedelta(days=1)
        works = lift(planned=True, head="Athy - Lift out of order")
        short = lift(planned=True, start="2026-08-02T09:00:00")
        fault = lift(planned=False, start="2026-08-03T09:00:00")
        self.poll(T0, [works])
        self.poll(T0 + long, [works, short])
        self.poll(T0 + long + timedelta(days=1), [works, short, fault])
        self.poll(T0 + long + timedelta(days=2), [works, short, fault])
        cells = self.cells(self.load())["cells"]
        # 9 Aug: the long works alone, past the grace by the time it came down
        self.assertEqual(cells[8], "6")
        # 16 Aug: the short works sit under the long one, which still wins
        self.assertEqual(cells[15], "6")
        # 17 Aug: the fault joins them and takes the day
        self.assertEqual(cells[16], "1")

    def test_a_notice_seen_only_at_the_last_poll_still_counts_that_day(self):
        # first_seen, end and the horizon coincide: a zero-minute listing.
        # It has to appear in the month's count, the day bar and the shard
        # alike, or the reader counts rows and comes up one short.
        self.poll(T0, [])
        self.poll(T0 + timedelta(hours=1), [lift()])
        outages = self.load()
        s = self.cells(outages)
        self.assertEqual(s["faults"], 1)
        self.assertEqual(s["cells"][7], "1")
        self.assertTrue(s["ongoing"])
        self.assertEqual(model.national_month(outages, "2026-08", NOW, self.until)["avail"], 0)
        self.assertEqual(len(render.shard(outages, ["2026-08"], self.until)["2026-08"]), 1)

    def test_a_reissue_does_not_repaint_the_days_before_it(self):
        # A planned-works notice replaced in the same poll by a fault: the days
        # already observed as planned works stay blue, and only the days after
        # the swap are red. The outage still reports the newest works flag.
        fault = lift(planned=False, head="Athy - Lifts out of order")
        self.poll(T0, [lift(planned=True)])
        swap = T0 + timedelta(days=2)
        self.poll(swap, [lift(planned=True)])
        self.poll(swap + timedelta(minutes=30), [fault])
        self.poll(swap + timedelta(days=1), [fault])
        outages = self.load()
        (o,) = outages
        self.assertFalse(o.planned)
        s = self.cells(outages)
        self.assertEqual(s["cells"][7:9], "55")  # 8-9 Aug: planned works only
        # 10 Aug carries both notices and a fault beats planned works; 11 Aug
        # is the fault alone. Before the fix all five days read as faults.
        self.assertEqual(s["cells"][9:11], "11")

    def test_a_day_past_the_build_clock_counts_against_nothing(self):
        """The bar stops at `now`; the window stops at the horizon. The Pi
        writes the run times and the builder reads its own clock, so an hour of
        skew puts the horizon ahead of `now` - and a day listed there was being
        counted against a total that excluded it, which took availability below
        zero and crashed the band lookup."""
        self.poll(T0, [lift()])
        self.poll(T0 + timedelta(days=3), [lift()])
        outages = self.load()
        # the horizon is two days past the build clock, so two listed days are
        # drawn as still to come and are not among the days that were watched
        s = self.cells(outages, now=T0 + timedelta(days=1))
        self.assertEqual(s["cells"][9:11], "99")
        self.assertLessEqual(s["against"], s["observed"])
        self.assertEqual((s["observed"], s["against"]), (2, 2))
        self.assertEqual((s["avail"], s["grade"]), (0, "F"))

    def test_planned_works_reissued_within_the_grace_still_run_past_it(self):
        """The grace is the notice's, not each folded segment's. Irish Rail
        reissue - that is what merge_edits exists for - and works reissued every
        few days are still works that ran for a fortnight."""
        planned = lift(planned=True)
        self.poll(T0, [planned])
        swap = T0 + timedelta(days=5)
        self.poll(swap, [planned])
        # a reissue at the very poll the old notice vanished: one outage, two
        # segments, neither of them longer than the grace on its own
        self.poll(swap + timedelta(minutes=30), [lift(planned=True, start="2026-08-13T09:00:00")])
        self.poll(swap + timedelta(days=5), [lift(planned=True, start="2026-08-13T09:00:00")])
        (o,) = outages = self.load()
        self.assertEqual(len(o.segments), 2)
        for seg_start, seg_end, _ in o.segments:
            self.assertLess(seg_end - seg_start, model.PLANNED_GRACE)
        s = self.cells(outages)
        self.assertEqual(s["avail"], 0)
        self.assertEqual(s["grade"], "F")

    def test_a_fault_after_the_works_does_not_retract_their_grace(self):
        """The grace is the works', measured over the planned segments alone.
        A fault that replaces them and runs on is the fault's doing, and the
        days it costs are its own - it cannot reach back and charge for a week
        of maintenance that had already been forgiven."""
        planned = lift(planned=True)
        self.poll(T0, [planned])
        swap = T0 + timedelta(days=6)
        self.poll(swap, [planned])
        fault = lift(text="The lift is currently out of service.", start="2026-08-14T09:00:00")
        self.poll(swap + timedelta(minutes=30), [fault])
        self.poll(swap + timedelta(days=3), [fault])
        (o,) = outages = self.load()
        self.assertEqual(len(o.segments), 2)
        s = self.cells(outages)
        # the four fault days count; the seven of works do not
        self.assertEqual(s["against"], 4)
        self.assertEqual((s["avail"], s["grade"]), (60, "E"))

    def test_ongoing_is_only_true_in_the_horizons_month(self):
        self.poll(T0, [lift()])
        self.poll(datetime(2026, 9, 2, tzinfo=UTC), [lift()])
        now = datetime(2026, 9, 3, tzinfo=UTC)
        outages = self.load(now=now)
        self.assertFalse(self.cells(outages, "2026-08", now=now)["ongoing"])
        self.assertTrue(self.cells(outages, "2026-09", now=now)["ongoing"])

    def test_the_row_says_which_kinds_are_listed_now(self):
        # A mask, not a bool: the tag beside the name has to say "Lift out" or
        # "Escalator out", and the sort treats any nonzero the same.
        self.poll(T0, [lift()])
        self.poll(T0 + timedelta(hours=1), [lift()])
        self.assertEqual(self.cells(self.load())["now"], model.NOW_KIND["lift"])
        self.poll(T0 + timedelta(hours=2), [lift(), escalator(code="ATHY", station="Athy")])
        self.assertEqual(self.cells(self.load())["now"], 3)
        self.drop(T0 + timedelta(hours=3))
        self.assertEqual(self.cells(self.load())["now"], 0)

    def test_the_month_headline_counts_stations_and_their_availability(self):
        self.poll(T0, [lift(), escalator(), lift(code="BRAY", station="Bray")])
        # Two polls without them, both still the 9th in Dublin: a third day
        # watched would change what this counts.
        self.poll(T0 + timedelta(days=1), [lift()])
        self.poll(T0 + timedelta(days=1, hours=1), [lift()])
        outages = self.load()
        n = model.national_month(outages, "2026-08", NOW, self.until)
        self.assertEqual(n["stations"], 3)
        self.assertEqual(n["outages"], 3)
        self.assertEqual((n["faults"], n["planned"]), (3, 0))
        # Two days watched at each of the three stations. Athy is listed
        # throughout and Bray closed at the poll on the 9th having been listed
        # into it; Connolly's escalator is on its own bar and off the total. So
        # two of the six station-days are available, floored.
        self.assertEqual(n["avail"], 33)
        self.assertEqual(n["ongoing"], 1)

    def test_a_past_month_counts_the_stations_listed_when_it_ended(self):
        """Issue #36: the "still out when the month ended" tile read 0 for
        every past month, because the predicate could only be true in the
        horizon's month. Athy runs into September and stays up, Tullamore runs
        into September and closes there, Bray closes inside August: two
        stations were listed when August ended."""
        aug = [lift(), lift(code="TMORE", station="Tullamore"), lift(code="BRAY", station="Bray")]
        self.poll(T0, aug)
        self.poll(T0 + timedelta(days=2), aug[:2])
        self.poll(datetime(2026, 9, 1, 9, 0, tzinfo=UTC), aug[:1])
        self.poll(datetime(2026, 9, 2, tzinfo=UTC), aug[:1])
        now = datetime(2026, 9, 3, tzinfo=UTC)
        outages = self.load(now=now)
        n = model.national_month(outages, "2026-08", now, self.until)
        self.assertEqual(n["stations"], 3)
        self.assertEqual(n["ongoing"], 2)
        # and September's own count is only what is still up at the horizon
        self.assertEqual(model.national_month(outages, "2026-09", now, self.until)["ongoing"], 1)


class TestPartialDays(unittest.TestCase):
    def test_the_first_and_last_days_are_flagged(self):
        # Dublin days, like the bars: 23:01 UTC is already the 18th in Dublin.
        until = datetime(2026, 8, 17, 23, 1, tzinfo=UTC)
        self.assertEqual(model.partial_days(until), ["2026-08-08", "2026-08-18"])

    def test_a_horizon_on_midnight_flags_the_day_before(self):
        # Midnight *in Dublin*, which in August is 23:00 the day before in UTC.
        until = datetime(2026, 8, 17, 23, 0, tzinfo=UTC)
        self.assertEqual(model.partial_days(until), ["2026-08-08", "2026-08-17"])


class TestMonthList(unittest.TestCase):
    def test_a_build_clock_before_the_first_poll_still_has_a_month(self):
        # --now takes any date a hand types, and every caller indexes the list
        self.assertEqual(
            model.month_list(model.COLLECTION_START, datetime(2026, 7, 15, tzinfo=UTC)),
            ["2026-08"],
        )

    def test_it_runs_from_the_start_month_to_the_end_month(self):
        self.assertEqual(
            model.month_list(model.COLLECTION_START, datetime(2026, 10, 2, tzinfo=UTC)),
            ["2026-08", "2026-09", "2026-10"],
        )


class TestShard(SiteModelCase):
    def test_an_outage_is_filed_under_every_month_it_was_listed_in(self):
        self.poll(T0, [lift()])
        self.poll(datetime(2026, 9, 2, tzinfo=UTC), [lift()])
        outages = self.load(now=datetime(2026, 9, 3, tzinfo=UTC))
        by_month = render.shard(outages, ["2026-08", "2026-09"], self.until)
        self.assertEqual(sorted(by_month), ["2026-08", "2026-09"])
        self.assertIs(by_month["2026-08"][0], by_month["2026-09"][0])

    def test_the_record_carries_both_clocks(self):
        self.poll(T0, [lift(start="2026-05-05T00:00:00")])
        (o,) = self.load()
        k = render.case_record(o)
        # [id, kind, planned, first_seen, end, ongoing, start, listed_end, head, text, updates]
        self.assertEqual(k[1], "lift")
        self.assertEqual(k[3], "2026-08-08T22:30")  # Dublin wall-clock
        self.assertEqual(k[6], "2026-05-05T00:00")  # as Irish Rail wrote it
        self.assertEqual(k[5], 1)
        self.assertEqual(k[7], "2026-12-31T23:59")  # still up: their end still means something

    def test_the_listed_end_goes_when_the_notice_does(self):
        # Irish Rail's end dates are placeholders near the end of the year. On
        # a notice that has come down, "listed end 30 Dec" reads as if the
        # works were still running; the notice coming down is the signal.
        self.poll(T0, [lift()])
        self.drop(T0 + timedelta(hours=1))
        (o,) = self.load()
        self.assertIsNone(render.case_record(o)[7])


class TestGrade(unittest.TestCase):
    def test_the_bands_meet_where_they_say_they_do(self):
        self.assertEqual(
            [model.grade(a) for a in (100, 99, 95, 94, 90, 89, 75, 74, 50, 49, 0)],
            ["A", "B", "B", "C", "C", "D", "D", "E", "E", "F", "F"],
        )

    def test_the_scale_runs_a_to_f_inclusive(self):
        """A scale that skips E is an American-ism, and Irish Rail is not
        American. E is up to half the month listed; F is more than half."""
        self.assertEqual([letter for _, letter in model.GRADE_BANDS], list("ABCDEF"))

    def test_a_month_nobody_watched_has_no_availability_and_no_grade(self):
        self.assertIsNone(model.availability(0, 0))
        self.assertIsNone(model.grade(None))

    def test_availability_is_floored_so_only_a_quiet_month_reads_a_hundred(self):
        self.assertEqual(model.availability(365, 1), 99)
        self.assertEqual(model.availability(31, 1), 96)
        self.assertEqual(model.availability(31, 0), 100)


if __name__ == "__main__":
    unittest.main()


class TestTheCollectorChecks(SiteModelCase):
    """Two things the build prints because the page cannot show them."""

    def test_a_reworded_head_is_caught_by_the_text_it_carries(self):
        self.poll(T0, [
            lift(),
            lift(
                head="Athy - Lift unavailable", text="The lift at platform 2 is out of service."
            ),
            lift(head="Service delay +15", text="Due to a signal fault.", codes=["X"]),
            lift(
                head="Customer notice", text="Escalators at Connolly are being replaced.",
                codes=["Y"],
            ),
        ])
        self.store.conn.commit()
        missed = model.unclassified_mentions(self.dir / "lift_status.db")
        self.assertEqual(
            [head for head, _ in missed], ["Athy - Lift unavailable", "Customer notice"]
        )

    def test_the_classifier_finds_every_head_the_mention_check_finds(self):
        # The guard is wider than the classifier or it checks nothing.
        for head in ("Skerries - Lifts out of order", "Connolly - Escalator out of Service"):
            self.assertTrue(model.MENTION.search(head), head)
            self.assertIsNotNone(model.classify(head), head)

    def test_a_day_with_few_polls_is_named_and_the_short_ends_are_not(self):
        # The first day of collection is short by nature. The 10th had two polls
        # out of forty-eight; the 11th had a full day.
        self.poll(T0, [lift()])
        for i in range(2):
            at = datetime(2026, 8, 10, 12, 0, tzinfo=UTC) + i * timedelta(minutes=30)
            self.poll(at, [lift()])
        for i in range(48):
            self.poll(datetime(2026, 8, 11, 0, 0, tzinfo=UTC) + i * timedelta(minutes=30), [lift()])
        self.poll(datetime(2026, 8, 12, 9, 0, tzinfo=UTC), [lift()])
        self.load()
        thin = model.thin_days(self.dir / "lift_status.db", self.until)
        self.assertEqual(thin, [(datetime(2026, 8, 10).date(), 2)])
