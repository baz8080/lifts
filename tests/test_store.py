import itertools
import json
import os
import tempfile
import unittest
from pathlib import Path

from lift_status.store import Store, utc_now_iso
from tests.helpers import make_item

_run_counter = itertools.count()


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.store = Store(self.data_dir)
        # Deterministic default regardless of the environment the tests run in.
        os.environ.pop("LIFT_STATUS_GRACE_MISSES", None)

    def tearDown(self):
        self.store.conn.close()
        self._tmp.cleanup()

    def _run(self, items, observed_at=None):
        observed_at = observed_at or utc_now_iso()
        run_id = self.store.begin_run_success(f"run-{next(_run_counter)}", observed_at, 200)
        diff = self.store.diff_and_update_messages(run_id, observed_at, items)
        self.store.finalize_run(run_id, observed_at, len(items), 0, 0)
        return diff

    def _message(self, key):
        row = self.store.conn.execute(
            "SELECT * FROM messages WHERE identity_key = ?", (key,)
        ).fetchone()
        return dict(row) if row else None

    def _listings(self, key):
        return [
            (r["opened_at_utc"], r["last_seen_at_utc"], r["closed_at_utc"])
            for r in self.store.conn.execute(
                """SELECT l.* FROM listings l JOIN messages m ON m.id = l.message_id
                   WHERE m.identity_key = ? ORDER BY l.opened_at_utc, l.id""",
                (key,),
            )
        ]


class TestWriteRaw(StoreTestCase):
    def test_writes_one_jsonl_line(self):
        self.store.write_raw("run-1", "2026-08-08T12:00:00Z", 200, "[]", None)
        path = self.data_dir / "raw" / "messages-20260808.jsonl"
        self.assertTrue(path.exists())
        line = json.loads(path.read_text().strip())
        self.assertEqual(line["run_uuid"], "run-1")
        self.assertEqual(line["http_status"], 200)
        self.assertEqual(line["body"], "[]")
        self.assertIsNone(line["network_error"])

    def test_appends_multiple_lines_same_day(self):
        self.store.write_raw("run-1", "2026-08-08T12:00:00Z", 200, "[]", None)
        self.store.write_raw("run-2", "2026-08-08T12:30:00Z", 200, "[]", None)
        path = self.data_dir / "raw" / "messages-20260808.jsonl"
        lines = path.read_text().strip().splitlines()
        self.assertEqual(len(lines), 2)


class TestDiffAndUpdateMessages(StoreTestCase):
    def test_new_message_is_inserted_open(self):
        item = make_item()
        from lift_status.parse import derive_identity_key

        diff = self._run([item])
        self.assertEqual(diff["new"], 1)
        self.assertEqual(diff["closed"], 0)
        msg = self._message(derive_identity_key(item))
        self.assertEqual(msg["status"], "open")
        self.assertIsNone(msg["closed_at_utc"])

    def test_message_present_again_stays_open_and_refreshes_text(self):
        item = make_item(text="first wording")
        from lift_status.parse import derive_identity_key

        self._run([item])
        item2 = dict(item, text="updated wording")
        diff = self._run([item2])
        self.assertEqual(diff["new"], 0)
        msg = self._message(derive_identity_key(item))
        self.assertEqual(msg["status"], "open")
        self.assertEqual(msg["text_raw"], "updated wording")

    def test_absent_message_closes_after_the_default_grace(self):
        """Two misses, and it closes at the first of them, not the second."""
        item = make_item()
        from lift_status.parse import derive_identity_key

        self._run([item], observed_at="2026-08-08T12:00:00Z")
        self.assertEqual(self._run([], observed_at="2026-08-08T12:30:00Z")["closed"], 0)
        self.assertEqual(self._run([], observed_at="2026-08-08T13:00:00Z")["closed"], 1)
        msg = self._message(derive_identity_key(item))
        self.assertEqual(msg["status"], "closed")
        self.assertEqual(msg["closed_at_utc"], "2026-08-08T12:30:00Z")

    def test_grace_period_delays_closure(self):
        os.environ["LIFT_STATUS_GRACE_MISSES"] = "3"
        try:
            item = make_item()
            from lift_status.parse import derive_identity_key

            self._run([item], observed_at="2026-08-08T12:00:00Z")
            diff1 = self._run([], observed_at="2026-08-08T12:30:00Z")
            self.assertEqual(diff1["closed"], 0)
            msg = self._message(derive_identity_key(item))
            self.assertEqual(msg["status"], "open")
            self.assertEqual(msg["consecutive_misses"], 1)
            self.assertEqual(msg["missing_since_at_utc"], "2026-08-08T12:30:00Z")

            self.assertEqual(self._run([], observed_at="2026-08-08T13:00:00Z")["closed"], 0)
            diff2 = self._run([], observed_at="2026-08-08T13:30:00Z")
            self.assertEqual(diff2["closed"], 1)
            msg = self._message(derive_identity_key(item))
            self.assertEqual(msg["status"], "closed")
            # Backdated to first absence, not to when grace elapsed.
            self.assertEqual(msg["closed_at_utc"], "2026-08-08T12:30:00Z")
        finally:
            del os.environ["LIFT_STATUS_GRACE_MISSES"]

    def test_flap_within_grace_resets_and_never_closes(self):
        os.environ["LIFT_STATUS_GRACE_MISSES"] = "2"
        try:
            item = make_item()
            from lift_status.parse import derive_identity_key

            self._run([item], observed_at="2026-08-08T12:00:00Z")
            self._run([], observed_at="2026-08-08T12:30:00Z")  # 1st miss
            self._run([item], observed_at="2026-08-08T13:00:00Z")  # reappears
            msg = self._message(derive_identity_key(item))
            self.assertEqual(msg["status"], "open")
            self.assertEqual(msg["consecutive_misses"], 0)
            self.assertIsNone(msg["missing_since_at_utc"])
        finally:
            del os.environ["LIFT_STATUS_GRACE_MISSES"]

    def test_reopen_after_closure_increments_reopen_count(self):
        item = make_item()
        from lift_status.parse import derive_identity_key

        self._run([item], observed_at="2026-08-08T12:00:00Z")
        self._run([], observed_at="2026-08-08T12:30:00Z")
        self._run([], observed_at="2026-08-08T13:00:00Z")  # closes
        self._run([item], observed_at="2026-08-09T09:00:00Z")  # reopens, new incident
        msg = self._message(derive_identity_key(item))
        self.assertEqual(msg["status"], "open")
        self.assertIsNone(msg["closed_at_utc"])
        self.assertEqual(msg["reopen_count"], 1)

    def test_a_reopen_starts_a_second_listing_rather_than_extending_the_first(self):
        """The gap is the measurement, so it must survive into the database.

        Portlaoise was published as sixteen days listed when the notice was up
        for two, either side of a fortnight it was not on the feed at all: one
        `messages` row spanning both, because identity_key is UNIQUE.
        """
        item = make_item()
        from lift_status.parse import derive_identity_key

        self._run([item], observed_at="2026-08-08T12:00:00Z")
        self._run([], observed_at="2026-08-08T12:30:00Z")
        self._run([], observed_at="2026-08-08T13:00:00Z")  # closes
        self._run([item], observed_at="2026-08-22T09:00:00Z")  # back after a fortnight
        self.assertEqual(
            self._listings(derive_identity_key(item)),
            [
                ("2026-08-08T12:00:00Z", "2026-08-08T12:00:00Z", "2026-08-08T12:30:00Z"),
                ("2026-08-22T09:00:00Z", "2026-08-22T09:00:00Z", None),
            ],
        )

    def test_a_notice_seen_again_while_still_open_extends_its_listing(self):
        item = make_item()
        from lift_status.parse import derive_identity_key

        self._run([item], observed_at="2026-08-08T12:00:00Z")
        self._run([item], observed_at="2026-08-08T12:30:00Z")
        self.assertEqual(
            self._listings(derive_identity_key(item)),
            [("2026-08-08T12:00:00Z", "2026-08-08T12:30:00Z", None)],
        )

    def test_a_miss_inside_the_grace_does_not_split_the_listing(self):
        """Grace absorbs a flaky poll, so it must not read as a new outage."""
        item = make_item()
        from lift_status.parse import derive_identity_key

        os.environ["LIFT_STATUS_GRACE_MISSES"] = "2"
        try:
            self._run([item], observed_at="2026-08-08T12:00:00Z")
            self._run([], observed_at="2026-08-08T12:30:00Z")  # one miss, still open
            self._run([item], observed_at="2026-08-08T13:00:00Z")
        finally:
            del os.environ["LIFT_STATUS_GRACE_MISSES"]
        self.assertEqual(
            self._listings(derive_identity_key(item)),
            [("2026-08-08T12:00:00Z", "2026-08-08T13:00:00Z", None)],
        )

    def test_a_database_written_before_listings_existed_gains_a_span(self):
        """An in-place upgrade on the Pi keeps its database, and the new table
        is created empty. A notice already open then would otherwise have no
        span at all until it next closed."""
        item = make_item()
        from lift_status.parse import derive_identity_key

        self._run([item], observed_at="2026-08-08T12:00:00Z")
        self.store.conn.execute("DELETE FROM listings")  # the pre-upgrade shape
        self._run([item], observed_at="2026-08-08T12:30:00Z")
        self.assertEqual(
            self._listings(derive_identity_key(item)),
            [("2026-08-08T12:00:00Z", "2026-08-08T12:30:00Z", None)],
        )

    def test_duplicate_identical_items_are_deduped_not_double_counted(self):
        item = make_item()
        diff = self._run([item, dict(item)])
        self.assertEqual(diff["new"], 1)
        self.assertEqual(diff["duplicate_conflicts"], 0)
        total = self.store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        self.assertEqual(total, 1)

    def test_duplicate_conflicting_items_first_wins_and_logs_conflict(self):
        item_a = make_item(text="version A")
        item_b = dict(item_a, text="version B")
        from lift_status.parse import derive_identity_key

        diff = self._run([item_a, item_b])
        self.assertEqual(diff["new"], 1)
        self.assertEqual(diff["duplicate_conflicts"], 1)
        msg = self._message(derive_identity_key(item_a))
        self.assertEqual(msg["text_raw"], "version A")

    def test_location_codes_reordering_does_not_spuriously_close_or_open(self):
        item_a = make_item(codes=["MHIDE", "DUBP"])
        item_b = make_item(codes=["DUBP", "MHIDE"])  # same set, different order
        diff1 = self._run([item_a], observed_at="2026-08-08T12:00:00Z")
        diff2 = self._run([item_b], observed_at="2026-08-08T12:30:00Z")
        self.assertEqual(diff1["new"], 1)
        self.assertEqual(diff2["new"], 0)
        self.assertEqual(diff2["closed"], 0)
        total = self.store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        self.assertEqual(total, 1)

    def test_item_missing_identity_field_is_routed_to_unidentifiable(self):
        good = make_item(head="Good Station - Lift out of order")
        bad = make_item(head="Bad Station - Lift out of order")
        del bad["locationCodes"]
        diff = self._run([good, bad])
        self.assertEqual(diff["new"], 1)
        self.assertEqual(diff["unidentifiable"], 1)
        n = self.store.conn.execute("SELECT COUNT(*) FROM unidentifiable_items").fetchone()[0]
        self.assertEqual(n, 1)

    def test_unidentifiable_item_does_not_affect_other_open_messages(self):
        # A malformed item present alongside a genuinely still-open message
        # must not cause that open message to be treated as absent.
        good = make_item(head="Good Station - Lift out of order")
        from lift_status.parse import derive_identity_key

        self._run([good], observed_at="2026-08-08T12:00:00Z")
        bad = make_item(head="Bad Station - Lift out of order")
        del bad["locationCodes"]
        diff = self._run([good, bad], observed_at="2026-08-08T12:30:00Z")
        self.assertEqual(diff["closed"], 0)
        msg = self._message(derive_identity_key(good))
        self.assertEqual(msg["status"], "open")


if __name__ == "__main__":
    unittest.main()
