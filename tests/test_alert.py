"""The repeat window, and the one thing it must not do: swallow a first alert.

A fault of the same kind is suppressed for a day so a stuck condition does not
push every 30 minutes until the user mutes the topic. The window therefore has to
open on delivery and not on the attempt, because the attempt most likely to fail
is the first one after the collector stops.
"""

from __future__ import annotations

import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
from unittest import mock

from lift_status import alert

BANNER = "lift-status: the API key was rejected"


class TheRepeatWindowOpensOnDelivery(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.data_dir = Path(self._tmp.name)
        env = mock.patch.dict(
            "os.environ",
            {
                "LIFT_STATUS_DATA_DIR": str(self.data_dir),
                "LIFT_STATUS_ALERT_WEBHOOK": "https://ntfy.example/lift-status",
            },
        )
        env.start()
        self.addCleanup(env.stop)

    @property
    def marker(self):
        return self.data_dir / ".last-alert.json"

    def _send(self, message=BANNER, working=True, dedup=True):
        def urlopen(*args, **kwargs):
            if not working:
                raise OSError("Name or service not known")
            return mock.MagicMock()

        with mock.patch.object(urllib.request, "urlopen", urlopen):
            return alert.notify(message, dedup=dedup)

    def test_a_delivered_alert_suppresses_the_next_one(self):
        self.assertTrue(self._send())
        self.assertTrue(alert._suppressed(BANNER))

    def test_a_webhook_failure_does_not_start_the_window(self):
        # The 30-minute run after this one is the user's next chance to hear
        # that collection has stopped. Marking the attempt costs them a day.
        self.assertFalse(self._send(working=False))
        self.assertFalse(self.marker.exists())
        self.assertFalse(alert._suppressed(BANNER))

    def test_the_retry_after_a_failure_is_delivered_and_then_suppresses(self):
        self._send(working=False)
        self.assertTrue(self._send())
        self.assertTrue(alert._suppressed(BANNER))

    def _clean_runs(self, n):
        for _ in range(n):
            alert.note_clean_run()

    def test_a_recovery_that_holds_makes_the_same_fault_a_new_alert(self):
        self._send()
        self._clean_runs(alert.RECOVERED_AFTER_CLEAN_RUNS - 1)
        self.assertTrue(self.marker.exists())
        self._clean_runs(1)
        self.assertFalse(alert._suppressed(BANNER))

    def test_a_fault_flapping_between_clean_polls_stays_one_alert(self):
        with mock.patch.object(urllib.request, "urlopen") as urlopen:
            for _ in range(4):
                alert.fail(alert.unreachable_banner("timed out"), alert.EXIT_UNREACHABLE)
                self._clean_runs(alert.RECOVERED_AFTER_CLEAN_RUNS - 1)
        self.assertEqual(urlopen.call_count, 1)

    def test_a_failure_that_was_not_delivered_still_breaks_the_clean_stretch(self):
        self._send()
        self._clean_runs(alert.RECOVERED_AFTER_CLEAN_RUNS - 1)
        with mock.patch.object(urllib.request, "urlopen", side_effect=OSError("blip")):
            alert.fail("lift-status: the disk is full", alert.EXIT_STORAGE)
        self._clean_runs(1)
        self.assertTrue(alert._suppressed(BANNER))

    def _fail(self, *banners_and_codes):
        with mock.patch.object(urllib.request, "urlopen") as urlopen:
            for args in banners_and_codes:
                alert.fail(*args)
        return urlopen.call_count

    def test_the_same_kind_of_fault_with_a_different_raw_error_is_one_alert(self):
        delivered = self._fail(
            (alert.unreachable_banner("TimeoutError('timed out')"), alert.EXIT_UNREACHABLE),
            (alert.unreachable_banner("ConnectionRefusedError(111)"), alert.EXIT_UNREACHABLE),
        )
        self.assertEqual(delivered, 1)

    def test_a_second_rejected_key_is_news(self):
        delivered = self._fail(
            (alert.auth_banner("abcdef...1234", "401"), alert.EXIT_AUTH, "abcdef...1234"),
            (alert.auth_banner("abcdef...1234", "403"), alert.EXIT_AUTH, "abcdef...1234"),
            (alert.auth_banner("ghijkl...5678", "401"), alert.EXIT_AUTH, "ghijkl...5678"),
        )
        self.assertEqual(delivered, 2)

    def test_two_faults_at_once_do_not_take_turns_to_alert(self):
        unreachable = (alert.unreachable_banner("timed out"), alert.EXIT_UNREACHABLE)
        database = (alert.database_banner("/data", "malformed"), alert.EXIT_DATABASE)
        self.assertEqual(self._fail(*[unreachable, database] * 4), 2)

    def test_an_older_marker_shape_means_send(self):
        self.marker.write_text(json.dumps({"digest": "x", "sent_at": 1e12}), encoding="utf-8")
        self.assertFalse(alert._suppressed(BANNER))

    def test_a_different_kind_is_never_suppressed(self):
        delivered = self._fail(
            (alert.unreachable_banner("timed out"), alert.EXIT_UNREACHABLE),
            (alert.storage_banner("/data", "No space left on device"), alert.EXIT_STORAGE),
        )
        self.assertEqual(delivered, 2)

    def test_an_expired_window_sends_again(self):
        self._send()
        stale = json.loads(self.marker.read_text(encoding="utf-8"))
        stale["sent"] = {k: v - alert.ALERT_REPEAT_SECONDS - 1 for k, v in stale["sent"].items()}
        self.marker.write_text(json.dumps(stale), encoding="utf-8")
        self.assertFalse(alert._suppressed(BANNER))

    def test_test_alert_neither_reads_nor_writes_the_window(self):
        self._send()
        before = self.marker.read_text(encoding="utf-8")
        self.assertTrue(self._send("a test alert", dedup=False))
        self.assertEqual(self.marker.read_text(encoding="utf-8"), before)

    def test_an_unreadable_marker_means_send(self):
        # Best-effort: the marker is a convenience, and failing to read it must
        # never be the reason an outage goes unreported.
        self.marker.write_text("null", encoding="utf-8")
        self.assertFalse(alert._suppressed(BANNER))
        self.marker.write_text("{ truncated", encoding="utf-8")
        self.assertFalse(alert._suppressed(BANNER))

    def test_no_webhook_configured_is_not_a_delivery(self):
        with mock.patch.dict("os.environ", {"LIFT_STATUS_ALERT_WEBHOOK": ""}):
            self.assertFalse(alert.notify(BANNER))
        self.assertFalse(self.marker.exists())


if __name__ == "__main__":
    unittest.main()
