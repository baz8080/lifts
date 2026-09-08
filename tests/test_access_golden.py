"""The golden files, and the difference reporter, on documents small enough to read.

`TheGoldenFilesReplayWhatTheyPinned` is the guard itself: it replays the pinned
inputs through today's code and fails on anything that moved. It lives here and
not in `test_site_real.py` because it needs no `lifts-data` checkout, which is
the point - the version that read the live corpus was skipped on a bare clone and
red on everyone else's schedule.

The rest is what counts as a difference, decided here and nowhere else: what a
document holds and the other does not is corpus size and must pass, and
everything both describe must fail the moment it moves.
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

    def test_a_notice_the_corpus_no_longer_carries_is_not_a_difference(self):
        # Irish Rail rewords a live banner in place and `messages.text_raw` is
        # overwritten, so a pinned body going missing says nothing about the code.
        self.current["verdicts"] = [v for v in self.current["verdicts"] if v["code"] != "PERSE"]
        self.assertEqual(golden.differences(self.stored, self.current), [])

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

    def test_a_renamed_snapshot_is_not_a_difference(self):
        # It is provenance. The pinned prose is what the verdicts are derived
        # from, so a monthly refresh moves this name and nothing else.
        self.current["snapshot"] = "irishrail-20261001.jsonl"
        self.assertEqual(golden.differences(self.stored, self.current), [])

    def test_a_field_a_verdict_grew_or_lost_is_reported_like_a_station_field(self):
        self.verdict("PERSE")["quoted"] = "Lift or stairs to platform 2"
        del self.verdict("CNLLY")["leg"]
        self.assertEqual(golden.differences(self.stored, self.current), [
            "notice CNLLY escalator: leg: 'entrance' -> None",
            "notice PERSE lift: quoted: None -> 'Lift or stairs to platform 2'",
        ])

    def test_a_station_only_one_document_has_is_not_a_difference(self):
        del self.current["stations"]["PERSE"]
        self.assertEqual(golden.differences(self.stored, self.current), [])


class TheDocumentSurvivesTheFile(unittest.TestCase):
    """`differences` compares a fresh `build` with a parsed file, so a tuple or a
    set anywhere in `build`'s output would read as a change on every run."""

    def test_a_round_trip_through_json_is_the_same_document(self):
        built = document()
        parsed = json.loads(golden.dumps(built))
        self.assertEqual(parsed, built)
        self.assertEqual(golden.differences(parsed, built), [])

    def test_a_notice_with_no_body_sorts_beside_one_with_a_body(self):
        built = golden.build(facts(), [
            ("PERSE", "lift", "Pearse - Lift out of order", PEARSE),
            ("PERSE", "lift", "Pearse - Lift out of order", ""),
        ])
        self.assertEqual([v["text"] for v in built["verdicts"]], ["", PEARSE])
        self.assertEqual(golden.differences(json.loads(golden.dumps(built)), built), [])

    def test_the_document_pins_a_verdict_and_the_prose_it_rests_on(self):
        built = document()
        self.assertEqual(built["stations"]["CNLLY"]["lift_platforms"], ["6", "7"])
        pearse = next(v for v in built["verdicts"] if v["code"] == "PERSE")
        self.assertEqual((pearse["state"], pearse["platforms"]), ("lost", ["2"]))


class TheGoldenFilesReplayWhatTheyPinned(unittest.TestCase):
    """The guard. Every input it needs is in the file, so it never skips."""

    def replay(self, path):
        stored = json.loads(path.read_text(encoding="utf-8"))
        return stored, golden.build(golden.pinned_facts(stored), golden.pinned_notices(stored))

    def test_the_access_golden_file_is_what_the_derivation_says_today(self):
        stored, current = self.replay(golden.PATH)
        self.assertEqual(
            golden.differences(stored, current),
            [],
            f"the derivation no longer matches {golden.PATH.name}. If the change is "
            "intended, regenerate with `python -m lift_access --data-dir <data-dir> "
            "golden`, read the diff, and commit it with the change:\n  "
            + "\n  ".join(golden.differences(stored, current)),
        )

    def test_every_pinned_station_replays_into_a_station(self):
        # A pinned input that read back as nothing would drop its station, and
        # `differences` compares what both documents have, so it would pass.
        stored = json.loads(golden.PATH.read_text(encoding="utf-8"))
        self.assertEqual(len(golden.pinned_facts(stored).stations), len(stored["stations"]))

    def test_every_pinned_notice_replays_into_a_verdict(self):
        stored = json.loads(golden.PATH.read_text(encoding="utf-8"))
        _, current = self.replay(golden.PATH)
        self.assertEqual(len(current["verdicts"]), len(stored["verdicts"]))


if __name__ == "__main__":
    unittest.main()
