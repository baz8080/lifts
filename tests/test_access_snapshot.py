"""The snapshot layer: the payload resolver, and the file it writes.

One behaviour here matters beyond "it parses": a refresh that changes nothing
must produce a byte-identical file, or the monthly job opens a pull request
every month with no change in it.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from lift_access import fetch, snapshot

# A Nuxt payload in miniature: slot 2 is the cache-key map, and every value is
# an index into the flat list rather than the thing itself.
PAYLOAD = [
    {"data": 1},
    ["ShallowReactive", 2],
    {"station-station/athy-en-ie": 3, "kontentStations-en-ie": 12},
    {"stationCode": 4, "stationName": 5, "platformAccess": 6, "latitude": 9, "longitude": 10},
    "ATHY",
    "Athy",
    {"html": 7},
    "<p>Level to platform 1<br>Lift to platform 2</p>",
    None,
    "52.9924",
    "-6.9768",
    None,
    [13, 15],
    {"stationName": 5, "slug": 14},
    "station/athy",
    {"stationName": 16, "slug": 17},
    "Carlow",
    "station/carlow",
]


class ReadingAPayload(unittest.TestCase):
    def test_the_station_object_comes_back_with_its_references_followed(self):
        node = fetch.station_node(PAYLOAD)
        self.assertEqual(node["stationCode"], "ATHY")
        self.assertEqual(node["stationName"], "Athy")
        self.assertIn("Lift to platform 2", node["platformAccess"]["html"])

    def test_the_slug_list_is_every_station(self):
        self.assertEqual(fetch.station_slugs(PAYLOAD), ["athy", "carlow"])

    def test_a_payload_with_no_station_is_not_an_error(self):
        self.assertIsNone(fetch.station_node([{}, {}, {}]))
        self.assertEqual(fetch.station_slugs([{}, {}, {}]), [])

    def test_a_reference_cycle_terminates(self):
        # The menus in a real payload refer back to themselves.
        looping = [{}, {}, {"station-station/x-en-ie": 3}, {"self": 3}]
        self.assertIsNotNone(fetch.station_node(looping))


class WritingASnapshot(unittest.TestCase):
    def test_the_same_facts_twice_give_an_identical_file(self):
        # Otherwise the monthly job opens a PR every month with no change in it.
        records = [{"slug": "carlow", "http_status": 200}, {"slug": "athy", "http_status": 200}]
        with tempfile.TemporaryDirectory() as tmp:
            first = fetch.write_snapshot(Path(tmp) / "a.jsonl", records, "2026-08-30T00:00:00Z")
            second = fetch.write_snapshot(
                Path(tmp) / "b.jsonl", list(reversed(records)), "2026-08-30T00:00:00Z"
            )
            self.assertEqual(first.read_text(), second.read_text())

    def test_keys_are_sorted_the_way_the_raw_log_sorts_them(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = fetch.write_snapshot(
                Path(tmp) / "a.jsonl", [{"z": 1, "a": 2}], "2026-08-30T00:00:00Z"
            )
            line = path.read_text().splitlines()[0]
            self.assertLess(line.index('"a"'), line.index('"z"'))

    def test_a_truncated_line_does_not_lose_the_good_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.jsonl"
            path.write_text('{"code": "ATHY"}\n{"code": "CRL\n{"code": "THRLS"}\n')
            self.assertEqual(
                [r["code"] for r in fetch.load_records(path)], ["ATHY", "THRLS"]
            )


class APartialFetchIsRefused(unittest.TestCase):
    """A station missing from the snapshot is not a station without facts.

    It is a station whose published verdict silently becomes "unknown" and which
    drops out of the denominator, and `latest_snapshot` reads the newest file, so
    a partial one shadows the last good snapshot permanently.
    """

    def _run(self, failing, attempts=2):
        calls = []

        def stub(url, timeout=60):
            if url == fetch.INDEX_URL:
                return 200, json.dumps(PAYLOAD)
            slug = url.rsplit("/", 2)[-2]
            calls.append(slug)
            if slug in failing:
                raise OSError("HTTP Error 503: Service Unavailable")
            return 200, json.dumps({"slug": slug})

        original, fetch._get = fetch._get, stub
        delay, backoff = fetch.DELAY_SECONDS, fetch.BACKOFF_SECONDS
        fetch.DELAY_SECONDS = fetch.BACKOFF_SECONDS = 0
        try:
            return fetch.fetch_stations(log=lambda *a: None, attempts=attempts) + (calls,)
        finally:
            fetch._get, fetch.DELAY_SECONDS, fetch.BACKOFF_SECONDS = original, delay, backoff

    def test_a_failed_station_is_named_not_dropped(self):
        records, failed, _ = self._run({"carlow"})
        self.assertEqual([r["slug"] for r in records], ["athy"])
        self.assertIn("carlow", failed)
        self.assertIn("503", failed["carlow"])

    def test_it_retries_before_giving_up(self):
        _, _, calls = self._run({"carlow"}, attempts=3)
        self.assertEqual(calls.count("carlow"), 3)

    def test_a_clean_run_reports_nothing_failed(self):
        records, failed, _ = self._run(set())
        self.assertEqual(len(records), 2)
        self.assertEqual(failed, {})

    def test_a_body_that_is_not_utf8_is_reported_not_raised(self):
        # UnicodeDecodeError is a ValueError, so neither HTTPError nor OSError
        # catches it, and it would abort a run whose whole job is to say which
        # stations it could not get.
        def stub(url, timeout=60):
            if url == fetch.INDEX_URL:
                return 200, json.dumps(PAYLOAD)
            raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

        records, failed = self._raw(stub)
        self.assertEqual(records, [])
        self.assertIn("UnicodeDecodeError", failed["athy"])

    def test_an_index_that_is_not_json_is_reported_not_raised(self):
        # An HTML error page where the payload should be is a JSONDecodeError.
        records, failed = self._raw(lambda url, timeout=60: (200, "<html>502</html>"))
        self.assertEqual(records, [])
        self.assertIn("JSONDecodeError", failed["(station index)"])

    def _raw(self, stub):
        original, fetch._get = fetch._get, stub
        delay, backoff = fetch.DELAY_SECONDS, fetch.BACKOFF_SECONDS
        fetch.DELAY_SECONDS = fetch.BACKOFF_SECONDS = 0
        try:
            return fetch.fetch_stations(log=lambda *a: None, attempts=1)
        finally:
            fetch._get, fetch.DELAY_SECONDS, fetch.BACKOFF_SECONDS = original, delay, backoff

    def test_a_200_with_an_empty_body_counts_as_a_failure(self):
        # irishrail.ie answering with an empty payload is not a station with no
        # facts; snapshot.load skips empty bodies, so it would vanish silently.
        original, fetch._get = fetch._get, lambda url, timeout=60: (
            (200, json.dumps(PAYLOAD)) if url == fetch.INDEX_URL else (200, "")
        )
        delay, backoff = fetch.DELAY_SECONDS, fetch.BACKOFF_SECONDS
        fetch.DELAY_SECONDS = fetch.BACKOFF_SECONDS = 0
        try:
            records, failed = fetch.fetch_stations(log=lambda *a: None, attempts=1)
        finally:
            fetch._get, fetch.DELAY_SECONDS, fetch.BACKOFF_SECONDS = original, delay, backoff
        self.assertEqual(records, [])
        self.assertEqual(sorted(failed), ["athy", "carlow"])


class WithNoSnapshotAtAll(unittest.TestCase):
    """The site built without station facts for months and still has to."""

    def test_loading_a_directory_that_has_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            facts = snapshot.load(tmp)
            self.assertFalse(facts)
            self.assertEqual(facts.stations, {})

    def test_a_verdict_without_facts_is_unknown_not_a_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            facts = snapshot.load(tmp)
            result = facts.verdict("ATHY", "lift", "The lift at platform 2 is out of service.")
            self.assertEqual(result.state, "unknown")

    def test_the_newest_snapshot_is_the_one_used(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / snapshot.SNAPSHOT_DIR
            directory.mkdir()
            for stamp in ("20260101", "20260830", "20260501"):
                body = json.dumps(PAYLOAD)
                (directory / f"irishrail-{stamp}.jsonl").write_text(
                    json.dumps({"slug": "athy", "body": body}) + "\n"
                )
            facts = snapshot.load(tmp)
            self.assertTrue(facts.path.name.endswith("20260830.jsonl"))
            self.assertIn("ATHY", facts.stations)


if __name__ == "__main__":
    unittest.main()
