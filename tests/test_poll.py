import fcntl
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from lift_status import alert, poll
from lift_status.client import AuthError, TransientError
from lift_status.store import Store, utc_now_iso
from tests.helpers import FakeClient, make_item


class PollTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _message_count(self):
        with Store(self.data_dir) as store:
            return store.conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

    def _run_count(self):
        with Store(self.data_dir) as store:
            return store.conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0]


class TestApplyResponseNeverDiffsOnFailure(PollTestCase):
    """The core structural guarantee: diff_and_update_messages must be called
    zero times for every failure shape, and exactly once for a real success -
    the whole point being that a future edit accidentally adding a second,
    unguarded call site would be caught here rather than silently shipped."""

    def _spy(self):
        return mock.patch.object(Store, "diff_and_update_messages", autospec=True)

    def test_auth_error_never_diffs(self):
        with self._spy() as spy, Store(self.data_dir) as store:
            poll.apply_response(store, "r1", utc_now_iso(), 401, None, "AuthError(...)")
        spy.assert_not_called()

    def test_unreachable_never_diffs(self):
        with self._spy() as spy, Store(self.data_dir) as store:
            poll.apply_response(store, "r1", utc_now_iso(), None, None, "TransientError(...)")
        spy.assert_not_called()

    def test_5xx_never_diffs(self):
        with self._spy() as spy, Store(self.data_dir) as store:
            poll.apply_response(store, "r1", utc_now_iso(), 503, "<html>bad gateway</html>", None)
        spy.assert_not_called()

    def test_malformed_json_never_diffs(self):
        with self._spy() as spy, Store(self.data_dir) as store:
            poll.apply_response(store, "r1", utc_now_iso(), 200, "{not json", None)
        spy.assert_not_called()

    def test_not_a_list_never_diffs(self):
        with self._spy() as spy, Store(self.data_dir) as store:
            poll.apply_response(store, "r1", utc_now_iso(), 200, json.dumps({"messages": []}), None)
        spy.assert_not_called()

    def test_sub_400_status_with_no_body_never_diffs(self):
        # A 304/300 arrives as a sub-400 status with no body: it must classify
        # as a failure, not crash on json.loads(None).
        with self._spy() as spy, Store(self.data_dir) as store:
            result = poll.apply_response(store, "r1", utc_now_iso(), 304, None, "ApiError('304')")
        spy.assert_not_called()
        self.assertEqual(result.outcome, "unreachable")
        self.assertEqual(result.exit_code, alert.EXIT_UNREACHABLE)

    def test_genuine_success_diffs_exactly_once_even_when_empty(self):
        # An honest empty list is a real success and must still go through the
        # one true call site - this is what actually closes messages.
        with self._spy() as spy, Store(self.data_dir) as store:
            poll.apply_response(store, "r1", utc_now_iso(), 200, "[]", None)
        spy.assert_called_once()

    def test_success_with_items_diffs_exactly_once(self):
        body = json.dumps([make_item()])
        with self._spy() as spy, Store(self.data_dir) as store:
            poll.apply_response(store, "r1", utc_now_iso(), 200, body, None)
        spy.assert_called_once()


class TestApplyResponseFailuresLeaveMessagesUntouched(PollTestCase):
    """Belt-and-braces version of the above, checked at the data level instead
    of via a spy: after a run that opened two messages, every failure shape
    must leave both of them exactly as they were - specifically not closed."""

    def _seed_two_open_messages(self):
        with Store(self.data_dir) as store:
            run_id = store.begin_run_success("seed", utc_now_iso(), 200)
            items = [
                make_item(head="Station A - Lift out of order", codes=["AAA"]),
                make_item(head="Station B - Lift out of order", codes=["BBB"]),
            ]
            store.diff_and_update_messages(run_id, utc_now_iso(), items)
            store.finalize_run(run_id, utc_now_iso(), 2, 0, 0)

    def _open_count(self):
        with Store(self.data_dir) as store:
            return store.conn.execute(
                "SELECT COUNT(*) FROM messages WHERE status = 'open'"
            ).fetchone()[0]

    def test_auth_failure_leaves_open_messages_open(self):
        self._seed_two_open_messages()
        self.assertEqual(self._open_count(), 2)
        with Store(self.data_dir) as store:
            poll.apply_response(store, "r2", utc_now_iso(), 401, None, "boom")
        self.assertEqual(self._open_count(), 2)

    def test_not_a_list_leaves_open_messages_open(self):
        self._seed_two_open_messages()
        with Store(self.data_dir) as store:
            poll.apply_response(store, "r2", utc_now_iso(), 200, json.dumps({"oops": True}), None)
        self.assertEqual(self._open_count(), 2)

    def test_genuine_empty_list_does_close_them(self):
        # Contrast case: proves the two tests above aren't passing by accident
        # (e.g. a no-op diff function) - a real empty response DOES close.
        self._seed_two_open_messages()
        with Store(self.data_dir) as store:
            poll.apply_response(store, "r2", utc_now_iso(), 200, "[]", None)
        self.assertEqual(self._open_count(), 0)


class TestRunPollEndToEnd(PollTestCase):
    def test_success_writes_raw_log_and_messages(self):
        body = json.dumps([make_item()])
        client = FakeClient([(200, body)])
        code = poll.run_poll(self.data_dir, client=client)
        self.assertEqual(code, alert.EXIT_OK)
        self.assertEqual(self._message_count(), 1)
        raw_files = list((self.data_dir / "raw").glob("*.jsonl"))
        self.assertEqual(len(raw_files), 1)

    def test_auth_error_exits_2_and_writes_nothing_to_messages(self):
        client = FakeClient([AuthError("401 rejected", status=401)])
        code = poll.run_poll(self.data_dir, client=client)
        self.assertEqual(code, alert.EXIT_AUTH)
        self.assertEqual(self._message_count(), 0)
        self.assertEqual(self._run_count(), 1)  # failure is still recorded

    def test_transient_error_exits_3(self):
        client = FakeClient([TransientError("network down", status=None)])
        code = poll.run_poll(self.data_dir, client=client)
        self.assertEqual(code, alert.EXIT_UNREACHABLE)

    def test_schema_drift_on_extra_field_exits_4_but_still_tracks(self):
        item = make_item()
        item["surpriseField"] = "new!"
        client = FakeClient([(200, json.dumps([item]))])
        code = poll.run_poll(self.data_dir, client=client)
        self.assertEqual(code, alert.EXIT_SCHEMA_DRIFT)
        self.assertEqual(self._message_count(), 1)  # still tracked despite drift

    def test_lock_contention_writes_nothing_and_exits_ok(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        lock_path = self.data_dir / ".poll.lock"
        handle = lock_path.open("w")
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            client = FakeClient([(200, json.dumps([make_item()]))])
            code = poll.run_poll(self.data_dir, client=client)
            self.assertEqual(code, alert.EXIT_OK)
            self.assertEqual(client.calls, 0)  # never even got to fetch
            self.assertEqual(self._run_count(), 0)
        finally:
            handle.close()

    @unittest.skipIf(os.geteuid() == 0, "root bypasses permission checks")
    def test_unwritable_data_dir_exits_storage_code(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.data_dir, 0o500)
        try:
            client = FakeClient([(200, "[]")])
            code = poll.run_poll(self.data_dir, client=client)
            self.assertEqual(code, alert.EXIT_STORAGE)
        finally:
            os.chmod(self.data_dir, 0o700)


class TestMissingApiKey(PollTestCase):
    """No key configured is a config error, distinct from a rejected key: it
    must not fetch and must not record a run."""

    def test_poll_with_no_key_writes_nothing_and_never_fetches(self):
        client = FakeClient([(200, "[]")], api_key="")
        code = poll.run_poll(self.data_dir, client=client)
        self.assertEqual(code, alert.EXIT_AUTH)
        self.assertEqual(client.calls, 0)
        self.assertEqual(self._run_count(), 0)
        self.assertEqual(len(list((self.data_dir / "raw").glob("*.jsonl"))), 0)

    def test_check_with_no_key_never_fetches(self):
        client = FakeClient([(200, "[]")], api_key="")
        self.assertEqual(poll.run_check(client=client), alert.EXIT_AUTH)
        self.assertEqual(client.calls, 0)

    def test_missing_key_banner_is_not_the_rejected_key_banner(self):
        self.assertIn("NO API KEY CONFIGURED", alert.missing_key_banner())
        self.assertNotIn("no longer accepted", alert.missing_key_banner())


class TestRunCheck(PollTestCase):
    def test_success(self):
        client = FakeClient([(200, json.dumps([make_item()]))])
        code = poll.run_check(client=client)
        self.assertEqual(code, alert.EXIT_OK)

    def test_auth_error(self):
        client = FakeClient([AuthError("401 rejected", status=401)])
        code = poll.run_check(client=client)
        self.assertEqual(code, alert.EXIT_AUTH)


if __name__ == "__main__":
    unittest.main()
