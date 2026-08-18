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
from datetime import datetime, timezone
from pathlib import Path

from lift_site import model, render
from lift_status.store import DB_FILENAME

DATA_DIR = os.environ.get("LIFT_STATUS_DATA_DIR")
DB_PATH = Path(DATA_DIR) / DB_FILENAME if DATA_DIR else None


@unittest.skipUnless(DB_PATH and DB_PATH.exists(), "LIFT_STATUS_DATA_DIR with a rebuilt database")
class TestRealCorpus(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.now = datetime.now(timezone.utc)
        cls.outages, cls.until = model.load_outages(DB_PATH, cls.now)
        cls.conn = sqlite3.connect(str(DB_PATH))
        cls.conn.row_factory = sqlite3.Row
        cls._tmp = tempfile.TemporaryDirectory()
        cls.site = Path(cls._tmp.name)
        cls.data = render.write(cls.site, cls.outages, cls.now, cls.until)

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

    def test_every_lift_or_escalator_notice_is_on_the_site_exactly_once(self):
        rows = self.conn.execute("SELECT id, head FROM messages").fetchall()
        wanted = {r["id"] for r in rows if model.classify(r["head"])}
        # Merged reissues carry the id of their first notice; the rest of the
        # chain is inside `updates`. Count the ids the outages account for.
        seen = []
        for o in self.outages:
            seen.append(o.id)
        self.assertEqual(len(seen), len(set(seen)))
        # Every outage on the site came from a notice that is a lift/escalator.
        self.assertTrue(set(seen) <= wanted)
        # And every such notice is either an outage or folded into one.
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
