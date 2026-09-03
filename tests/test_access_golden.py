"""The golden file's difference reporter, on documents small enough to read.

The real-corpus test compares an in-memory `build` against the parsed file, so
what counts as a difference is decided here and nowhere else: a notice the file
has never seen must pass (the corpus gains one every few days), and everything
the file does hold must fail the moment it moves.
"""

from __future__ import annotations

import copy
import json
import unittest

from lift_access import golden, snapshot
from tests.test_access_model import ENTRY, PROSE, station

CONNOLLY = "The Escalator at the main concourse is out of order."
PEARSE = "The lift at platform 2 is out of order."


def facts():
    return snapshot.Facts(
        {code: station(code) for code in PROSE if code in ENTRY}, path=None
    )


def document():
    return golden.build(
        facts(),
        [
            ("CNLLY", "escalator", "Connolly - Escalator out of order", CONNOLLY),
            ("PERSE", "lift", "Pearse - Lift out of order", PEARSE),
        ],
    )


class TheDifferenceReporter(unittest.TestCase):
    def setUp(self):
        self.stored = document()
        self.current = copy.deepcopy(self.stored)

    def verdict(self, code):
        return next(v for v in self.current["verdicts"] if v["code"] == code)

    def test_identical_documents_do_not_differ(self):
        self.assertEqual(golden.differences(self.stored, self.current), [])

    def test_a_notice_the_file_has_not_seen_is_not_a_difference(self):
        self.current["verdicts"].append(
            {"code": "ATHY", "kind": "lift", "text": "The lift is out.", "state": "unknown",
             "leg": None, "platforms": [], "detail": "..."}
        )
        self.assertEqual(golden.differences(self.stored, self.current), [])
        self.assertEqual([v["code"] for v in golden.new_notices(self.stored, self.current)],
                         ["ATHY"])

    def test_a_notice_that_vanished_is_one_line(self):
        self.current["verdicts"] = [v for v in self.current["verdicts"] if v["code"] != "PERSE"]
        self.assertEqual(golden.differences(self.stored, self.current),
                         ["notice PERSE lift: dropped"])

    def test_a_moved_state_and_a_moved_detail_are_one_line_each(self):
        self.verdict("PERSE")["state"] = "unknown"
        self.verdict("CNLLY")["detail"] = "reworded"
        lines = golden.differences(self.stored, self.current)
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("notice CNLLY escalator: detail:"))
        self.assertTrue(lines[1].startswith("notice PERSE lift: state: 'lost' -> 'unknown'"))

    def test_a_moved_level_line_names_the_station_and_field(self):
        self.current["stations"]["CNLLY"]["step_free_platforms"] = []
        lines = golden.differences(self.stored, self.current)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("station CNLLY: step_free_platforms:"))

    def test_a_renamed_snapshot_is_a_difference_on_its_own(self):
        self.current["snapshot"] = "irishrail-20261001.jsonl"
        self.assertEqual(golden.differences(self.stored, self.current),
                         ["snapshot: None -> irishrail-20261001.jsonl"])

    def test_a_dropped_station_is_one_line(self):
        del self.current["stations"]["PERSE"]
        self.assertEqual(golden.differences(self.stored, self.current),
                         ["station PERSE: dropped"])


class TheDocumentSurvivesTheFile(unittest.TestCase):
    """`differences` compares a fresh `build` with a parsed file, so a tuple or a
    set anywhere in `build`'s output would read as a change on every run."""

    def test_a_round_trip_through_json_is_the_same_document(self):
        built = document()
        parsed = json.loads(golden.dumps(built))
        self.assertEqual(parsed, built)
        self.assertEqual(golden.differences(parsed, built), [])

    def test_the_document_pins_a_verdict_and_the_prose_it_rests_on(self):
        built = document()
        self.assertEqual(built["stations"]["CNLLY"]["lift_platforms"], ["6", "7"])
        pearse = next(v for v in built["verdicts"] if v["code"] == "PERSE")
        self.assertEqual((pearse["state"], pearse["platforms"]), ("lost", ["2"]))


if __name__ == "__main__":
    unittest.main()
