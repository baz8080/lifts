"""What an observation may look like, decided here and nowhere else."""

from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from lift_access import survey

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "survey" / "TOY.jsonl"

GOOD = {
    "code": "TOY", "observed": "2026-09-10", "confidence": "high",
    "source": {"kind": "survey", "by": "A. Surveyor"},
    "fact": {"type": "edge", "id": "up", "mode": "lift", "from": "hall", "to": "bridge",
             "equipment": "lift-a"},
}


def variant(**changes):
    obj = copy.deepcopy(GOOD)
    for key, value in changes.items():
        if key == "fact":
            obj["fact"] = value
        elif key == "source":
            obj["source"] = value
        else:
            obj[key] = value
    return obj


class Validation(unittest.TestCase):
    def test_every_fixture_line_validates(self):
        for line in FIXTURE.read_text(encoding="utf-8").splitlines():
            self.assertEqual(survey.validate(json.loads(line), "TOY"), [], line)

    def test_the_example_validates(self):
        self.assertEqual(survey.validate(GOOD, "TOY"), [])

    def assertRejected(self, obj, phrase, expected_code="TOY"):
        errors = survey.validate(obj, expected_code)
        self.assertTrue(any(phrase in e for e in errors), f"{phrase!r} not in {errors}")

    def test_unknown_fact_type(self):
        self.assertRejected(variant(fact={"type": "wall", "id": "x"}), "fact.type")

    def test_unknown_mode(self):
        self.assertRejected(
            variant(fact={"type": "edge", "id": "x", "mode": "zipline", "from": "a", "to": "b"}),
            "edge.mode",
        )

    def test_a_gate_needs_its_kind(self):
        self.assertRejected(
            variant(fact={"type": "edge", "id": "x", "mode": "gate", "from": "a", "to": "b"}),
            "gate",
        )

    def test_a_lift_edge_needs_its_equipment(self):
        self.assertRejected(
            variant(fact={"type": "edge", "id": "x", "mode": "lift", "from": "a", "to": "b"}),
            "equipment",
        )

    def test_a_page_source_needs_a_quote(self):
        self.assertRejected(
            variant(source={"kind": "irishrail-page", "snapshot": "s", "field": "platformAccess"}),
            "quote",
        )

    def test_an_empty_page_quote_is_allowed(self):
        # It records that the field said nothing usable, and expires when it does.
        obj = variant(source={"kind": "irishrail-page", "snapshot": "s",
                              "field": "platformAccess", "quote": ""})
        self.assertEqual(survey.validate(obj, "TOY"), [])

    def test_a_page_source_names_a_real_field(self):
        self.assertRejected(
            variant(source={"kind": "irishrail-page", "snapshot": "s", "field": "alert",
                            "quote": "x"}),
            "source.field",
        )

    def test_a_survey_needs_a_person(self):
        self.assertRejected(variant(source={"kind": "survey"}), "needs by")

    def test_a_bad_date(self):
        self.assertRejected(variant(observed="10/09/2026"), "observed")

    def test_a_bad_confidence(self):
        self.assertRejected(variant(confidence="certain"), "confidence")

    def test_kishoge_is_a_station_code(self):
        # The one code in the snapshot that is not upper case.
        self.assertEqual(survey.validate(variant(code="Kishoge"), "Kishoge"), [])

    def test_the_code_must_match_the_file(self):
        self.assertRejected(variant(code="ATHY"), "in a file for TOY")

    def test_a_platform_node_needs_its_label(self):
        self.assertRejected(variant(fact={"type": "node", "id": "p9", "kind": "platform"}),
                            "platform label")

    def test_ids_are_slugs(self):
        self.assertRejected(variant(fact={"type": "node", "id": "Platform 1", "kind": "platform",
                                          "platform": "1"}), "fact.id")

    def test_a_retract_names_what_it_retracts(self):
        self.assertRejected(variant(fact={"type": "retract", "id": "up"}), "retract.of")
        self.assertEqual(survey.validate(variant(fact={"type": "retract", "id": "up",
                                                        "of": "edge"}), "TOY"), [])

    def test_a_note_needs_text(self):
        self.assertRejected(variant(fact={"type": "note"}), "note")


class Files(unittest.TestCase):
    def test_dumps_is_one_sorted_line(self):
        text = survey.dumps(GOOD)
        self.assertEqual(text.count("\n"), 1)
        self.assertTrue(text.endswith("\n"))
        keys = list(json.loads(text))
        self.assertEqual(keys, sorted(keys))

    def test_load_reads_a_directory_and_skips_bad_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / survey.SURVEY_DIR
            directory.mkdir()
            (directory / "TOY.jsonl").write_text(
                survey.dumps(GOOD) + "not json\n" + survey.dumps(variant(code="ATHY")),
                encoding="utf-8",
            )
            data = survey.load(tmp)
            self.assertEqual([o.fact["id"] for o in data.observations["TOY"]], ["up"])
            self.assertEqual(len(data.problems), 2)
            self.assertIn(":2: not JSON", data.problems[0])
            self.assertIn(":3: ", data.problems[1])
            self.assertTrue(data)
            self.assertEqual(len(survey.digest(tmp)), 12)

    def test_no_directory_is_an_empty_survey(self):
        with tempfile.TemporaryDirectory() as tmp:
            data = survey.load(tmp)
            self.assertFalse(data)
            self.assertEqual(data.problems, [])
            self.assertIsNone(data.path)

    def test_the_digest_moves_when_a_line_lands(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp) / survey.SURVEY_DIR
            directory.mkdir()
            path = directory / "TOY.jsonl"
            path.write_text(survey.dumps(GOOD), encoding="utf-8")
            before = survey.digest(tmp)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(survey.dumps(variant(confidence="low")))
            self.assertNotEqual(before, survey.digest(tmp))
