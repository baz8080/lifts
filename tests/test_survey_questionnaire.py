"""The form asks what the data cannot answer, and shows what it can."""

from __future__ import annotations

import unittest

from lift_access import nta, questionnaire
from tests.test_access_model import station

PEARSE_NOTICES = [
    ("lift", "Dublin Pearse - Lift out of order", "The lift at platform 2 is out of order."),
    ("escalator", "Dublin Pearse - Escalator out of order", "The Escalator at platform 2 is out."),
    ("lift", "Dublin Pearse - Lift out of order", "The lift at platform 2 is out of order."),
]


class TheForm(unittest.TestCase):
    def setUp(self):
        self.pearse = questionnaire.render(station("PERSE"), PEARSE_NOTICES,
                                           snapshot_name="irishrail-20260901.jsonl")
        self.athy = questionnaire.render(station("ATHY"), [],
                                         snapshot_name="irishrail-20260901.jsonl")

    def test_it_quotes_both_fields(self):
        self.assertIn("> Ramp to platform 1 (City Centre and northbound)", self.pearse)
        self.assertIn("> Level, through main entrance to the booking hall", self.pearse)

    def test_it_says_how_the_site_reads_the_page(self):
        self.assertIn("A lift on the way to platform 2.", self.pearse)
        self.assertIn('Platform 1 reached without a lift: "Ramp to platform 1', self.pearse)
        self.assertIn('A lift on the way in: "Lifts/stairs/Escalators', self.pearse)

    def test_every_distinct_notice_is_asked_about_once(self):
        self.assertEqual(self.pearse.count("Dublin Pearse - Lift out of order"), 1)
        self.assertEqual(self.pearse.count("Dublin Pearse - Escalator out of order"), 1)
        self.assertIn("which machine is this", self.pearse.lower())

    def test_the_definitions_and_common_questions_come_first_and_last(self):
        self.assertLess(self.pearse.index("Read this first"),
                        self.pearse.index("Irish Rail's page"))
        self.assertIn("**When the lift is out.**", self.pearse)
        self.assertIn("un-assisted", self.pearse)

    def test_the_business_case_paragraph_appears_for_athy_and_not_pearse(self):
        self.assertIn("number 10 of the 51 stations", self.athy)
        self.assertIn(nta.CONTEXT["ATHY"][1][:60], self.athy)
        self.assertIn("Full Delivery (2025)", self.athy)
        self.assertIn("What has changed since?", self.athy)
        self.assertNotIn("Station Accessibility Programme said", self.pearse)

    def test_a_discrepancy_is_put_to_the_reader(self):
        limerick = questionnaire.render(station("LMRKJ"), [],
                                        snapshot_name="irishrail-20260901.jsonl")
        self.assertIn(questionnaire.PAGE_DISCREPANCIES["LMRKJ"], limerick)
        self.assertNotIn("disagree about", self.pearse)

    def test_the_draft_observations_are_in_the_form(self):
        self.assertIn('"id": "lift-p2"', self.pearse)
        self.assertIn("```", self.pearse)

    def test_no_em_dash(self):
        for text in (self.pearse, self.athy, questionnaire.DEFINITIONS, questionnaire.COMMON):
            self.assertNotIn("\u2014", text)
            self.assertNotIn("\u2013", text)
