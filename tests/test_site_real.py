"""The whole pipeline against the real corpus.

Skipped unless LIFT_STATUS_DATA_DIR points at a data directory holding a
rebuilt `lift_status.db` (normally a checkout of `lifts-data` after
`python -m lift_status --data-dir <it> rebuild`). CI sets it, so a change that
quietly drops notices on the floor or files them under the wrong month is
caught against data that has every wrinkle the synthetic tests do not.
"""

from __future__ import annotations

import calendar
import json
import os
import sqlite3
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from lift_access import fetch, snapshot
from lift_access import model as access_model
from lift_site import model, render
from lift_status.store import DB_FILENAME

DATA_DIR = os.environ.get("LIFT_STATUS_DATA_DIR")
DB_PATH = Path(DATA_DIR) / DB_FILENAME if DATA_DIR else None

# The station snapshot lives in the same data repository but lands separately,
# and the site is built to work without it. So these skip the way the rest of
# this file skips, rather than failing a checkout that has not got it yet.
SNAPSHOT_PATH = (
    fetch.latest_snapshot(Path(DATA_DIR) / snapshot.SNAPSHOT_DIR, snapshot.STATIONS_PREFIX)
    if DATA_DIR
    else None
)


@unittest.skipUnless(DB_PATH and DB_PATH.exists(), "LIFT_STATUS_DATA_DIR with a rebuilt database")
class TestRealCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.now = datetime.now(UTC)
        cls.outages, cls.until = model.load_outages(DB_PATH, cls.now)
        cls.conn = sqlite3.connect(str(DB_PATH))
        cls.conn.row_factory = sqlite3.Row
        cls._tmp = tempfile.TemporaryDirectory()
        cls.site = Path(cls._tmp.name)
        cls.facts = snapshot.load(DATA_DIR)
        cls.data = render.write(cls.site, cls.outages, cls.now, cls.until, cls.facts)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        cls._tmp.cleanup()

    def test_the_horizon_is_the_last_run_that_reached_the_feed(self):
        row = self.conn.execute(
            "SELECT MAX(started_at_utc) AS t FROM runs WHERE outcome = 'ok'"
        ).fetchone()
        self.assertEqual(self.until, model.parse_utc(row["t"]))
        self.assertLessEqual(model.COLLECTION_START, self.until)

    def test_every_listing_span_is_on_the_site_exactly_once(self):
        # Spans, not notices: a notice that came back must reach the site as
        # two outages, or the gap is republished as listed time.
        rows = self.conn.execute(
            """SELECT l.id AS id, m.head AS head
               FROM listings l JOIN messages m ON m.id = l.message_id"""
        ).fetchall()
        wanted = {r["id"] for r in rows if model.classify(r["head"])}
        # Merged reissues carry the id of their first span; the rest of the
        # chain is inside `updates`. Count the ids the outages account for.
        seen = []
        for o in self.outages:
            seen.append(o.id)
        self.assertEqual(len(seen), len(set(seen)))
        # Every outage on the site came from a notice that is a lift/escalator.
        self.assertTrue(set(seen) <= wanted)
        # And every such span is either an outage or folded into one.
        folded = sum(len(o.updates) for o in self.outages)
        self.assertEqual(len(seen) + folded, len(wanted))

    def test_the_shards_add_up_to_the_headline(self):
        for ym in self.data["months"]:
            n = self.data["national"][ym]
            listed = set()
            for code in self.data["stations"]:
                text = (self.site / "h" / f"{code}.js").read_text(encoding="utf-8")
                shard = json.loads(text.split("= ", 1)[1].rstrip(";\n"))
                for k in shard.get(ym, []):
                    listed.add(k[0])
            self.assertEqual(len(listed), n[1], ym)

    def test_the_station_list_and_the_stats_agree(self):
        for code, per_month in self.data["stats"].items():
            self.assertIn(code, self.data["stations"])
            for ym, m in per_month.items():
                year, month = int(ym[:4]), int(ym[5:7])
                self.assertEqual(len(m[0]), calendar.monthrange(year, month)[1])
                self.assertGreater(m[1] + m[2], 0)

    def test_the_first_day_of_collection_is_no_data_before_it_and_data_after(self):
        cells = self.data["blank"]["2026-08"]
        self.assertEqual(cells[:7], "8888888")
        self.assertIn(cells[7], "0")

    def test_initial_load_is_inside_the_budget(self):
        total, _ = render.size_report(self.site)
        self.assertLess(total, render.BUDGET_BYTES)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(DB_PATH and DB_PATH.exists() and SNAPSHOT_PATH, "a station snapshot")
class TestAccessVerdictsOnTheRealCorpus(unittest.TestCase):
    """Every verdict the site would publish today, checked against the snapshot.

    The rule this guards is one-directional: the site may understate access as
    often as it likes, and may say it cannot tell, but it may never tell a
    reader another step-free way exists unless Irish Rail's own prose says so at
    that platform. See notes/station-access.md.
    """

    @classmethod
    def setUpClass(cls):
        cls.now = datetime.now(UTC)
        cls.outages, cls.until = model.load_outages(DB_PATH, cls.now)
        cls.facts = snapshot.load(DATA_DIR)

    def test_the_snapshot_covers_the_network(self):
        # Every station on the railway, not the handful with a notice this month.
        self.assertGreater(len(self.facts.stations), 100)

    def test_every_notice_gets_a_verdict(self):
        states = {"lost", "alternative", "escalator", "unknown"}
        for o in self.outages:
            result = self.facts.verdict(o.code, o.kind, o.text)
            self.assertIn(result.state, states, o.head)

    def test_no_outage_claims_an_alternative_without_a_reviewed_entry(self):
        for o in self.outages:
            result = self.facts.verdict(o.code, o.kind, o.text)
            if result.state != "alternative":
                continue
            for platform in result.platforms:
                self.assertIn(
                    (o.code, platform),
                    access_model.STEP_FREE_ALTERNATIVES,
                    f"{o.code} platform {platform} claimed an alternative that nobody reviewed",
                )

    def test_every_reviewed_alternative_still_matches_the_live_page(self):
        # The entries quote sentences off station pages that are refetched every
        # month precisely because Irish Rail rewords them. This is the check that
        # notices; the model withdraws the claim on its own, but silently.
        for (code, platform), quoted in access_model.STEP_FREE_ALTERNATIVES.items():
            station = self.facts.station(code)
            if station is None:
                continue
            prose = " ".join((station.platform_access or "").split())
            self.assertIn(
                quoted,
                prose,
                f"{code} platform {platform}: the reviewed sentence is gone from the page. "
                "Read it again and update or drop the entry.",
            )

    def test_an_escalator_never_removes_step_free_access(self):
        for o in self.outages:
            if o.kind != "escalator":
                continue
            self.assertEqual(self.facts.verdict(o.code, o.kind, o.text).state, "escalator")

    def test_an_escalator_notice_only_lands_where_the_page_claims_a_lift(self):
        # An escalator that is the only powered way up is the one escalator
        # outage that should knock the grade, and no station has been of that
        # shape. notes/site.md § The grade is lift availability. A station
        # missing from the snapshot is "unknown", not "no", and is the previous
        # test's failure rather than this one's.
        for o in self.outages:
            if o.kind != "escalator":
                continue
            self.assertNotEqual(
                self.facts.has_lift(o.code),
                "no",
                f"{o.station} ({o.code}) has an escalator notice and a page that claims no "
                "lift: the only-powered-way-up case. Build the rule in "
                "lift_site.model.station_month rather than loosening this test.",
            )

    def test_every_station_with_a_lift_notice_is_in_the_snapshot(self):
        # locationCodes and irishrail.ie's stationCode are the same code space.
        # If that ever stops being true this is where it shows up.
        missing = sorted({o.code for o in self.outages} - set(self.facts.stations))
        self.assertEqual(missing, [], "notice codes with no station in the snapshot")

    def test_the_kept_platform_note_never_overclaims(self):
        # Issue #31's weaker claim, held to the same one-directional rule: the
        # sentence is on the live page, and neither the notice nor the page puts
        # the platform behind a lift.
        for o in self.outages:
            station = self.facts.station(o.code)
            result = self.facts.verdict(o.code, o.kind, o.text)
            if "kept step-free access" not in result.detail:
                continue
            self.assertEqual(result.state, "lost", o.head)
            self.assertNotIn(access_model.ALL_PLATFORMS, station.lift_platforms, o.head)
            for platform, sentence in access_model.step_free_platforms(station):
                if f'"{sentence}"' not in result.detail:
                    continue
                self.assertIn(sentence, station.platform_access, o.head)
                self.assertNotIn(platform, result.platforms, o.head)
                self.assertNotIn(platform, station.lift_platforms, o.head)
                self.assertNotIn(platform, access_model.affected_platforms(o.text), o.head)

    def test_only_a_lost_verdict_says_a_platform_kept_access(self):
        for o in self.outages:
            result = self.facts.verdict(o.code, o.kind, o.text)
            if result.state != "lost":
                self.assertNotIn("kept step-free access", result.detail, o.head)

    def test_the_verdict_reaches_the_shard(self):
        months = model.month_list(model.COLLECTION_START, max(self.now, self.until))
        for o in self.outages[:5]:
            by_month = render.shard([o], months, self.until, self.facts)
            records = [r for rows in by_month.values() for r in rows]
            self.assertTrue(records, o.head)
            self.assertIsNotNone(records[0][13], o.head)
