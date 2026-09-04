"""The passenger-facing layout can say everything the graph can."""

from __future__ import annotations

import unittest

from lift_access import graph, prose, seed, survey
from tests.test_access_model import PROSE, station
from tests.test_survey_graph import build, line


class Layout(unittest.TestCase):
    def test_the_toy_station_reads_as_promised(self):
        g, _ = build()
        text = prose.render(g)
        self.assertIn("Getting to the platforms without steps", text)
        self.assertIn("Platform 1: yes. A level walk to the booking hall, then a level walk to "
                      "platform 1.", text)
        self.assertIn("Platform 2: yes, by lift.", text)
        self.assertIn("If the lift is out of service there is no step-free way to platform 2.",
                      text)
        self.assertIn("Platform 3: yes, by lift. A level walk to the booking hall, then a lift "
                      "to platform 3. If the lift is out of service the page names a way round "
                      "(a level walk to the booking hall, then a ramp to platform 3) that "
                      "nobody has confirmed.", text)
        self.assertIn("The main entrance: level to the booking hall", text)
        self.assertIn("Three lifts.", text)
        self.assertIn("called from a help point, 06:00-23:30", text)
        self.assertIn("Still to record", text)

    def test_a_platform_with_no_step_free_way_says_no_and_how_it_is_reached(self):
        g, _ = build([line({"type": "retract", "id": "to-p1", "of": "edge"}),
                      line({"type": "edge", "id": "p1-stairs", "mode": "stairs", "from": "hall",
                            "to": "p1", "stair_count": 12})])
        text = prose.render(g)
        self.assertIn("Platform 1: no. It is reached by stairs from the booking hall.", text)

    def test_a_confirmed_way_round_the_lift_is_said(self):
        g, _ = build([line({"type": "edge", "id": "ramp-p3", "mode": "ramp", "from": "hall",
                            "to": "p3"})])
        text = prose.render(g)
        self.assertIn("Platform 3: yes. A level walk to the booking hall, then a ramp to "
                      "platform 3.", text)

    def test_a_page_only_route_is_said_to_be_unconfirmed(self):
        g, _ = build([line({"type": "retract", "id": "lift-to-p3", "of": "edge"})])
        text = prose.render(g)
        self.assertIn("Platform 3: yes, according to Irish Rail's page, which nobody has "
                      "confirmed. A level walk to the booking hall, then a ramp to platform 3.",
                      text)

    def test_an_unsurveyed_way_in_is_said_as_not_yet_recorded(self):
        g, _ = build([line({"type": "edge", "id": "back", "mode": "unsurveyed", "from": "side",
                            "to": "hall"})])
        text = prose.render(g)
        self.assertIn("is not yet recorded", text)
        self.assertIn("Platform 1: yes.", text)

    def test_every_mode_and_kind_present_appears_in_the_output(self):
        for code in PROSE:
            lines = seed.observations(station(code), "irishrail-20260901.jsonl")
            g, _ = graph.replay([survey.observation(o, i + 1) for i, o in enumerate(lines)])
            text = prose.render(g, station(code))
            for edge in g.edges.values():
                self.assertIn(prose.WORDS[edge.mode].split()[-1], text, (code, edge.id))
            for node in g.nodes.values():
                if node.kind == "platform":
                    self.assertIn(f"Platform {node.platform}", text, code)
            self.assertNotIn("\u2014", text)
