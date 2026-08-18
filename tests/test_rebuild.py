"""The most important test in this project: the raw JSONL log is the source of
truth and the SQLite database is disposable, so a rebuild from the log alone
must reproduce identical message state. This test drives a realistic run
history - opens, a refresh, a close, a failed run in between (which must not
disturb anything), a reopen, a duplicate, and an unidentifiable item - through
the real run_poll() entry point, then wipes the database and rebuilds it, and
compares the two snapshots on natural keys.
"""

import json
import tempfile
import unittest
from pathlib import Path

from lift_status import poll
from lift_status.client import AuthError
from lift_status.store import Store
from tests.helpers import FakeClient, make_item

STATION_A = make_item(head="Station A - Lift out of order", codes=["AAA"])
STATION_B = make_item(head="Station B - Lift out of order", codes=["BBB"])
STATION_C = make_item(head="Station C - Lift out of order", codes=["CCC"])


def _snapshot(data_dir) -> dict:
    with Store(data_dir) as store:
        rows = store.conn.execute(
            """SELECT identity_key, head, text_raw, start_raw, start_utc, end_raw, end_utc,
                      location_codes, products, event_stops, tz_ambiguous,
                      first_seen_at_utc, last_seen_at_utc, status, consecutive_misses,
                      missing_since_at_utc, closed_at_utc, reopen_count
               FROM messages ORDER BY identity_key"""
        ).fetchall()
        messages = {r["identity_key"]: dict(r) for r in rows}

        run_rows = store.conn.execute(
            "SELECT outcome, http_status, item_count, schema_drift_count, error_detail, exit_code "
            "FROM runs ORDER BY started_at_utc, run_uuid"
        ).fetchall()
        runs = [dict(r) for r in run_rows]

        unidentifiable = store.conn.execute(
            "SELECT reason FROM unidentifiable_items ORDER BY reason"
        ).fetchall()
        unidentifiable = [dict(r) for r in unidentifiable]

    return {"messages": messages, "runs": runs, "unidentifiable": unidentifiable}


class TestRebuildRoundTrip(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_synthetic_history_round_trips_through_rebuild(self):
        # 1. Baseline: A and B open.
        poll.run_poll(self.data_dir, client=FakeClient([(200, json.dumps([STATION_A, STATION_B]))]))

        # 2. B repeated verbatim, A's text updated - still open, refreshed.
        a_updated = dict(STATION_A, text="Update: engineers on site.")
        poll.run_poll(self.data_dir, client=FakeClient([(200, json.dumps([a_updated, STATION_B]))]))

        # 3. B disappears -> closes. A duplicate of A (identical) is also
        #    present and must not be double-counted.
        poll.run_poll(self.data_dir, client=FakeClient([(200, json.dumps([a_updated, dict(a_updated)]))]))

        # 4. A transient auth failure - must leave A/B state completely alone.
        poll.run_poll(self.data_dir, client=FakeClient([AuthError("401", status=401)]))

        # 5. B reappears (a fresh, unrelated breakdown) -> reopened. An
        #    unidentifiable item (missing locationCodes) rides along and must
        #    not disturb A or B.
        broken = make_item(head="Station D - Lift out of order")
        del broken["locationCodes"]
        poll.run_poll(
            self.data_dir,
            client=FakeClient([(200, json.dumps([a_updated, STATION_B, broken]))]),
        )

        # 6. A malformed JSON response - another failure that must change
        #    nothing.
        poll.run_poll(self.data_dir, client=FakeClient([(200, "{not valid json")]))

        # 7. A not-a-list response - same guarantee.
        poll.run_poll(self.data_dir, client=FakeClient([(200, json.dumps({"oops": True}))]))

        # 8. Station C opens fresh, with an unexpected extra field (schema
        #    drift), still tracked despite the drift.
        c_drifted = dict(STATION_C, newField="surprise")
        poll.run_poll(self.data_dir, client=FakeClient([(200, json.dumps([a_updated, STATION_B, c_drifted]))]))

        before = _snapshot(self.data_dir)

        # Sanity check the scenario actually exercised what it claims to.
        self.assertEqual(len(before["messages"]), 3)  # A, B, C (broken excluded)
        statuses = {k: v["status"] for k, v in before["messages"].items()}
        self.assertEqual(list(statuses.values()).count("open"), 3)
        self.assertEqual(len(before["unidentifiable"]), 1)
        outcomes = [r["outcome"] for r in before["runs"]]
        self.assertEqual(outcomes.count("auth_error"), 1)
        self.assertEqual(outcomes.count("parse_error"), 1)
        self.assertEqual(outcomes.count("not_a_list"), 1)
        self.assertEqual(outcomes.count("ok"), 5)

        code = poll.run_rebuild(self.data_dir)
        after = _snapshot(self.data_dir)

        self.assertEqual(code, 0)
        self.assertEqual(before["messages"], after["messages"])
        self.assertEqual(before["runs"], after["runs"])
        self.assertEqual(before["unidentifiable"], after["unidentifiable"])

    def test_rebuild_with_no_raw_logs_is_a_harmless_noop(self):
        code = poll.run_rebuild(self.data_dir)
        self.assertEqual(code, 0)
        snap = _snapshot(self.data_dir)
        self.assertEqual(snap["messages"], {})
        self.assertEqual(snap["runs"], [])


if __name__ == "__main__":
    unittest.main()
