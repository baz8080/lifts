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
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lift_site import model, render
from lift_status.store import Store
from tests.helpers import make_item

_run_counter = itertools.count()

# A synthetic collection that starts where the real one did.
T0 = model.COLLECTION_START
NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)


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
        self.poll(gone, [])
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
        self.assertEqual(o.start, datetime(2026, 5, 4, 23, 0, tzinfo=timezone.utc))
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
        # A corrected start changes the identity key too.
        self.poll(T0, [lift(start="2026-08-05T09:00:00")])
        self.poll(T0 + timedelta(minutes=30), [lift(start="2026-08-01T09:00:00", planned=True)])
        (o,) = self.load()
        self.assertEqual(o.start, datetime(2026, 8, 1, 8, 0, tzinfo=timezone.utc))
        self.assertTrue(o.planned)

    def test_a_notice_that_comes_back_a_poll_later_is_a_separate_outage(self):
        self.poll(T0, [lift()])
        self.poll(T0 + timedelta(minutes=30), [])
        self.poll(T0 + timedelta(minutes=60), [lift(start="2026-08-09T09:00:00")])
        outages = self.load()
        self.assertEqual(len(outages), 2)
        self.assertEqual([o.ongoing for o in outages], [True, False])  # newest first

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
        self.poll(T0 + timedelta(days=2), [])
        s = self.cells(self.load())
        self.assertEqual(len(s["cells"]), 31)
        # 1-7 August: before collection. 8-10: listed, the 10th only until the
        # horizon at 21:30. 11-20: no data (the 20th has begun by `now`, so it
        # is not "still to come"). 21 onwards is after `now`.
        self.assertEqual(s["cells"][:7], "8" * 7)
        self.assertEqual(s["cells"][7:10], "111")
        self.assertEqual(s["cells"][10:20], "8" * 10)
        self.assertEqual(s["cells"][20:], "9" * 11)
        self.assertEqual((s["faults"], s["planned"], s["days_out"]), (1, 0, 3))
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
        self.assertEqual(s["days_out"], 0)

    def test_a_fault_beats_planned_works_and_a_lift_beats_an_escalator(self):
        fault = lift(text="The lift is currently out of service.", start="2026-08-02T00:00:00")
        self.poll(T0, [lift(planned=True), escalator(), fault])
        self.poll(T0 + timedelta(hours=2), [lift(planned=True), escalator(), fault])
        outages = self.load()
        s = self.cells(outages)
        self.assertEqual(s["cells"][7], "1")
        # Only the escalator and the planned lift: escalator colours the day.
        s = self.cells([o for o in outages if o.kind == "escalator" or o.planned])
        self.assertEqual(s["cells"][7], "2")
        s = self.cells([o for o in outages if o.planned])
        self.assertEqual(s["cells"][7], "5")

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
        self.assertEqual(model.national_month(outages, "2026-08", self.until)["station_days"], 1)
        self.assertEqual(len(render.shard(outages, ["2026-08"], self.until)["2026-08"]), 1)

    def test_ongoing_is_only_true_in_the_horizons_month(self):
        self.poll(T0, [lift()])
        self.poll(datetime(2026, 9, 2, tzinfo=timezone.utc), [lift()])
        now = datetime(2026, 9, 3, tzinfo=timezone.utc)
        outages = self.load(now=now)
        self.assertFalse(self.cells(outages, "2026-08", now=now)["ongoing"])
        self.assertTrue(self.cells(outages, "2026-09", now=now)["ongoing"])

    def test_the_month_headline_counts_stations_and_station_days(self):
        self.poll(T0, [lift(), escalator(), lift(code="BRAY", station="Bray")])
        self.poll(T0 + timedelta(days=1, hours=1), [lift()])
        outages = self.load()
        n = model.national_month(outages, "2026-08", self.until)
        self.assertEqual(n["stations"], 3)
        self.assertEqual(n["outages"], 3)
        self.assertEqual((n["faults"], n["planned"]), (3, 0))
        # Athy: 8th and 9th. Connolly and Bray: 8th and 9th too - closed at
        # the poll on the 9th, having been listed into it.
        self.assertEqual(n["station_days"], 6)
        self.assertEqual(n["ongoing"], 1)


class TestPartialDays(unittest.TestCase):
    def test_the_first_and_last_days_are_flagged(self):
        until = datetime(2026, 8, 17, 23, 1, tzinfo=timezone.utc)
        self.assertEqual(model.partial_days(until), ["2026-08-08", "2026-08-17"])

    def test_a_horizon_on_midnight_flags_the_day_before(self):
        until = datetime(2026, 8, 18, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(model.partial_days(until), ["2026-08-08", "2026-08-17"])


class TestShard(SiteModelCase):
    def test_an_outage_is_filed_under_every_month_it_was_listed_in(self):
        self.poll(T0, [lift()])
        self.poll(datetime(2026, 9, 2, tzinfo=timezone.utc), [lift()])
        outages = self.load(now=datetime(2026, 9, 3, tzinfo=timezone.utc))
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


if __name__ == "__main__":
    unittest.main()
