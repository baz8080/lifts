"""The replay, the reachability and the verdict, on a station drawn by hand.

TOY has a main entrance level to the booking hall, a side gate a wheelchair
does not fit through, platform 1 level from the hall, platform 2 up a lift or
stairs to a footbridge and down another lift or stairs, and platform 3 by a
lift or by a ramp that only the page vouches for.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from lift_access import graph, survey
from tests.test_access_model import station

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "survey" / "TOY.jsonl"
FORBIDDEN = ("still had", "remains", "was working", "available", "unaffected")


def observations(extra=()):
    lines = [json.loads(line) for line in FIXTURE.read_text(encoding="utf-8").splitlines()]
    lines.extend(extra)
    return [survey.observation(obj, i + 1) for i, obj in enumerate(lines)]


def line(fact, confidence="high", source=None, observed="2026-09-11"):
    return {"code": "TOY", "observed": observed, "confidence": confidence,
            "source": source or {"kind": "survey", "by": "B. Surveyor"}, "fact": fact}


def build(extra=(), station_facts=None):
    return graph.replay(observations(extra), station_facts)


class Replay(unittest.TestCase):
    def test_the_fixture_replays_cleanly(self):
        g, problems = build()
        self.assertEqual(problems, [])
        self.assertTrue(g.complete)
        self.assertEqual(sorted(g.platforms()), ["1", "2", "3"])
        self.assertEqual(g.entrances(), ("main", "side"))
        self.assertEqual(len(g.notes), 1)

    def test_the_last_line_for_a_key_wins(self):
        g, _ = build([line({"type": "edge", "id": "to-p1", "mode": "stairs", "from": "hall",
                            "to": "p1", "stair_count": 6})])
        self.assertEqual(g.edges["to-p1"].mode, "stairs")
        self.assertEqual(g.edges["to-p1"].observed, "2026-09-11")

    def test_a_retract_removes_the_fact(self):
        g, problems = build([line({"type": "retract", "id": "ramp-p3", "of": "edge"})])
        self.assertNotIn("ramp-p3", g.edges)
        self.assertEqual(problems, [])

    def test_retracting_nothing_is_reported(self):
        _, problems = build([line({"type": "retract", "id": "ghost", "of": "edge"})])
        self.assertEqual(len(problems), 1)
        self.assertIn("ghost", problems[0])

    def test_a_dangling_endpoint_is_reported(self):
        _, problems = build([line({"type": "edge", "id": "x", "mode": "walkway",
                                   "from": "hall", "to": "nowhere"})])
        self.assertTrue(any("nowhere" in p for p in problems))

    def test_an_edge_of_the_wrong_kind_for_its_equipment_is_reported(self):
        _, problems = build([line({"type": "edge", "id": "x", "mode": "escalator",
                                   "from": "hall", "to": "p1", "equipment": "lift-a"})])
        self.assertTrue(any("is a escalator but lift-a is a lift" in p for p in problems))

    def test_an_unsurveyed_edge_makes_the_graph_incomplete(self):
        g, _ = build([line({"type": "edge", "id": "back-door", "mode": "unsurveyed",
                            "from": "side", "to": "hall"})])
        self.assertFalse(g.complete)

    def test_a_page_fact_whose_quote_left_the_page_is_dropped(self):
        facts = station("ATHY")  # "Level to platform 1 / Lift to platform 2": no ramp to 3
        g, problems = build(station_facts=facts)
        self.assertNotIn("ramp-p3", g.edges)
        self.assertTrue(any("ramp-p3" in p and "no longer" in p for p in problems))

    def test_an_empty_quote_expires_when_the_field_says_something(self):
        empty = line({"type": "edge", "id": "way-in", "mode": "unsurveyed", "from": "main",
                      "to": "hall"}, "low",
                     {"kind": "irishrail-page", "snapshot": "s", "field": "ticketOfficeAccess",
                      "quote": ""})
        g, problems = build([empty], station("ATHY"))  # its way in is "Level from ..."
        self.assertEqual(g.edges["way-in"].mode, "walkway")  # the fixture's line survived
        self.assertTrue(any("way-in" in p for p in problems))


class Reachability(unittest.TestCase):
    def setUp(self):
        self.g, _ = build()

    def test_every_platform_is_step_free_today(self):
        reached = graph.step_free_platforms(self.g)
        self.assertEqual(sorted(reached), ["1", "2", "3"])
        self.assertEqual(reached["1"], ("way-in", "to-p1"))
        self.assertEqual(reached["2"], ("way-in", "up", "down"))

    def test_the_route_with_the_fewest_lifts_is_the_one_described(self):
        self.assertEqual(graph.step_free_platforms(self.g)["3"], ("way-in", "ramp-p3"))

    def test_a_gate_a_wheelchair_does_not_fit_is_not_step_free(self):
        self.assertFalse(graph.step_free(self.g.edges["side-gate"]))
        self.assertNotIn("side-gate", graph.step_free_platforms(self.g)["3"])

    def test_removing_the_lift_loses_platform_2_and_keeps_1(self):
        without = graph.reachable(self.g, frozenset({"up"}))
        self.assertIn("p1", without)
        self.assertNotIn("p2", without)

    def test_lift_platforms_are_the_ones_a_lift_edge_touches(self):
        self.assertEqual(graph.lift_platforms(self.g), ("2", "3"))

    def test_describe_route_reads_as_a_sentence(self):
        text = graph.describe_route(self.g, ("way-in", "up", "down"))
        self.assertEqual(
            text, "a level walk to the booking hall, then a lift to the footbridge, "
                  "then a lift to platform 2",
        )


class Joining(unittest.TestCase):
    def setUp(self):
        self.g, _ = build()

    def test_by_platform(self):
        self.assertEqual(graph.join_notice(self.g, "lift", "The lift at platform 2 is out."),
                         (("lift-b",), ()))

    def test_by_alias(self):
        self.assertEqual(graph.join_notice(self.g, "lift", "The big lift is out of order."),
                         (("lift-a",), ()))

    def test_a_named_platform_no_lift_touches_is_unmatched(self):
        self.assertEqual(graph.join_notice(self.g, "lift", "The lift at platform 1 is out."),
                         ((), ("1",)))

    def test_an_unlocated_notice_is_every_lift(self):
        joined, _ = graph.join_notice(self.g, "lift", "The lift is out of service.")
        self.assertEqual(joined, ("lift-a", "lift-b", "lift-c"))

    def test_an_entrance_leg_notice_is_the_lifts_touching_an_entrance(self):
        g, _ = build([
            line({"type": "equipment", "id": "lift-door", "kind": "lift"}),
            line({"type": "edge", "id": "door", "mode": "lift", "from": "main", "to": "hall",
                  "equipment": "lift-door"}),
        ])
        joined, _ = graph.join_notice(g, "lift", "The lift at the main concourse is out.")
        self.assertEqual(joined, ("lift-door",))


class Verdicts(unittest.TestCase):
    def check(self, result):
        for phrase in FORBIDDEN:
            self.assertNotIn(phrase, result.detail.lower(), result.detail)
        self.assertIn(result.state, graph.STATES)
        return result

    def test_a_lift_on_the_only_route_loses_the_platform(self):
        g, _ = build()
        result = self.check(graph.verdict(g, "lift", "The lift at platform 2 is out of order."))
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ("2",))
        self.assertIn("Platform 2 is reached by the lift between the footbridge and platform 2",
                      result.detail)
        self.assertIn("Platforms 1 and 3 never needed this lift.", result.detail)
        self.assertEqual(result.leg, "platform")

    def test_a_lift_higher_up_the_chain_loses_the_platform_too(self):
        g, _ = build()
        result = self.check(graph.verdict(g, "lift", "The big lift is out of order."))
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ("2",))

    def test_a_route_only_the_page_vouches_for_does_not_count(self):
        g, _ = build()
        result = self.check(graph.verdict(g, "lift", "The lift at platform 3 is out."))
        self.assertEqual(result.state, "lost")
        self.assertEqual(result.platforms, ("3",))
        self.assertIn("nobody has confirmed", result.detail)
        self.assertIn('Irish Rail\'s page: "Ramp or lift to platform 3"', result.detail)

    def test_a_confirmed_route_round_the_lift_is_an_alternative(self):
        g, _ = build([line({"type": "edge", "id": "ramp-p3", "mode": "ramp", "from": "hall",
                            "to": "p3", "slope": 8})])
        result = self.check(graph.verdict(g, "lift", "The lift at platform 3 is out."))
        self.assertEqual(result.state, "alternative")
        self.assertEqual(result.platforms, ("3",))
        self.assertIn("Platform 3 kept a step-free way: a level walk to the booking hall, "
                      "then a ramp to platform 3.", result.detail)

    def test_every_quote_in_a_detail_is_an_observation_quote(self):
        g, _ = build()
        quotes = {o.source.get("quote") for o in observations() if "quote" in o.source}
        for text in ("The lift at platform 3 is out.", "The lift at platform 2 is out."):
            detail = graph.verdict(g, "lift", text).detail
            for quote in __import__("re").findall(r'"([^"]+)"', detail):
                self.assertIn(quote, quotes)

    def test_an_escalator_names_the_lift_beside_it(self):
        g, _ = build()
        result = self.check(graph.verdict(g, "escalator", "The escalator is out of order."))
        self.assertEqual(result.state, "escalator")
        self.assertIn("did lose a way up", result.detail)
        self.assertIn("records a lift between the booking hall and the footbridge as well",
                      result.detail)

    def test_an_escalator_with_nothing_beside_it_says_so(self):
        g, _ = build([
            line({"type": "equipment", "id": "esc-b", "kind": "escalator"}),
            line({"type": "edge", "id": "esc-to-p1", "mode": "escalator", "from": "hall",
                  "to": "p1", "equipment": "esc-b"}),
        ])
        result = graph.verdict(g, "escalator", "The escalator at platform 1 is out.")
        self.assertIn("records no lift between the booking hall and platform 1", result.detail)

    def test_nothing_joined_is_unknown(self):
        g, _ = build()
        result = self.check(graph.verdict(g, "lift", "The lift at platform 1 is out."))
        self.assertEqual(result.state, "unknown")
        self.assertIn("records no lift matching this notice", result.detail)
        self.assertIn("lift-a, lift-b, lift-c", result.detail)

    def test_no_survey_is_unknown(self):
        result = graph.verdict(graph.StationGraph("X", {}, {}, {}, {}, (), True), "lift", "x")
        self.assertEqual(result.state, "unknown")

    def test_a_platform_never_reached_is_said_softly_when_incomplete(self):
        g, _ = build([
            line({"type": "node", "id": "p4", "kind": "platform", "platform": "4"}),
            line({"type": "edge", "id": "p4-stairs", "mode": "stairs", "from": "hall",
                  "to": "p4"}),
            line({"type": "edge", "id": "back-door", "mode": "unsurveyed", "from": "side",
                  "to": "hall"}),
        ])
        result = graph.verdict(g, "lift", "The lift at platform 2 is out.")
        self.assertIn("Platform 4 has no step-free route on the survey, which is incomplete.",
                      result.detail)

    def test_the_unmatched_platform_is_named(self):
        g, _ = build()
        result = graph.verdict(g, "lift", "The lift at platforms 1 and 2 is out.")
        self.assertEqual(result.state, "lost")
        self.assertIn("also names platform 1, which no recorded lift touches", result.detail)


class Contradictions(unittest.TestCase):
    def test_a_clean_graph_has_none(self):
        g, _ = build()
        self.assertEqual(graph.contradictions(g), [])

    def test_equipment_with_no_edge(self):
        g, _ = build([line({"type": "equipment", "id": "lift-z", "kind": "lift"})])
        self.assertIn("lift lift-z is recorded but no edge belongs to it",
                      graph.contradictions(g))

    def test_equipment_on_both_legs(self):
        g, _ = build([line({"type": "edge", "id": "odd", "mode": "lift", "from": "main",
                            "to": "hall", "equipment": "lift-c"})])
        self.assertIn("lift lift-c is on both the platforms and the way in",
                      graph.contradictions(g))

    def test_a_level_platform_on_the_page_with_no_route_in_the_survey(self):
        g, _ = build([line({"type": "retract", "id": "to-p1", "of": "edge"})])
        found = graph.contradictions(g, station("ATHY"))
        self.assertTrue(any("platform 1 level" in f for f in found), found)
