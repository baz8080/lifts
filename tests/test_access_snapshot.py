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
