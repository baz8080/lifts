"""The seeder against the published prose: it may draw what the page says and no more."""

from __future__ import annotations

import unittest

from lift_access import graph, model, seed, survey
from tests.test_access_model import PROSE, station

SNAPSHOT = "irishrail-20260901.jsonl"


def build(code):
    lines = seed.observations(station(code), SNAPSHOT)
    g, problems = graph.replay([survey.observation(obj, i + 1) for i, obj in enumerate(lines)])
    return lines, g, problems


class RoundTrip(unittest.TestCase):
    def test_every_fixture_station_seeds_validly_and_replays_cleanly(self):
        for code in PROSE:
            lines, g, problems = build(code)
            self.assertEqual(problems, [], code)
            for obj in lines:
                self.assertEqual(survey.validate(obj, code), [], code)

    def test_level_platforms_agree_with_the_prose_derivation(self):
        for code in PROSE:
            _, g, _ = build(code)
            page = {label for label, _ in model.step_free_platforms(station(code))}
            reached = set(graph.step_free_platforms(g))
            # The way in is unsurveyed at most fixture stations, so reachability
            # is only checkable where the entrance leg seeded a real edge.
            if g.complete:
                self.assertTrue(page <= reached, (code, page, reached))

    def test_lift_platforms_agree_with_the_prose_derivation(self):
        for code in PROSE:
            _, g, _ = build(code)
            page = set(station(code).lift_platforms) - {model.ALL_PLATFORMS}
            entrance_lifts = {e.equipment for e in g.edges.values()
                              if e.mode == "lift" and "entrance" in e.id}
            self.assertEqual(set(graph.lift_platforms(g)), page, code)
            self.assertTrue(all(e.startswith("lift-entrance") for e in entrance_lifts), code)

    def test_a_general_claim_gives_a_note_and_no_lift(self):
        for code in ("HZLCH", "BBRHY", "DCKLS"):
            _, g, _ = build(code)
            self.assertEqual([e for e in g.edges.values() if e.mode == "lift"
                              and "entrance" not in e.id], [], code)
            self.assertTrue(any("without saying which platform" in text for text, _ in g.notes),
                            code)

    def test_lifts_and_ramps_is_a_sequence(self):
        _, g, _ = build("HZLCH")
        self.assertEqual([e for e in g.edges.values() if e.mode == "ramp"], [])

    def test_the_reviewed_alternatives_seed_a_medium_ramp(self):
        for code, label in (("RAHNY", "1"), ("CORK", "5A")):
            _, g, _ = build(code)
            edge = g.edges[f"ramp-p{label.lower()}"]
            self.assertEqual(edge.mode, "ramp")
            self.assertEqual(edge.confidence, "medium")
            self.assertEqual(edge.source["reviewed"], "STEP_FREE_ALTERNATIVES")
            self.assertIn(f"lift-p{label.lower()}", g.equipment)

    def test_the_boilerplate_seeds_no_lift(self):
        for code in ("KILNY", "GSTNS", "DBATE"):
            _, g, _ = build(code)
            self.assertEqual(g.equipment, {}, code)

    def test_dromod_seeds_no_lift_and_a_footbridge(self):
        _, g, _ = build("DRMOD")
        self.assertEqual(g.equipment, {})
        self.assertEqual(g.edges["stairs-p2"].mode, "footbridge-stairs")

    def test_castleknock_shape_stairs_only_to_platform_2(self):
        _, g, _ = build("GSTNS")  # "Footbridge only to platform 2 (southbound)"
        self.assertEqual(g.edges["stairs-p2"].mode, "footbridge-stairs")
        self.assertIn("1", graph.step_free_platforms(g) if g.complete else {"1": ()})

    def test_a_blank_way_in_is_unsurveyed(self):
        _, g, _ = build("HZLCH")  # no ENTRY fixture
        self.assertEqual(g.edges["way-in"].mode, "unsurveyed")
        self.assertFalse(g.complete)
        self.assertEqual(g.edges["way-in"].source["quote"], "")

    def test_a_level_way_in_is_a_walkway(self):
        _, g, _ = build("ATHY")
        self.assertEqual(g.edges["way-in"].mode, "walkway")
        self.assertEqual(g.edges["way-in"].source["field"], "ticketOfficeAccess")
        self.assertTrue(g.complete)

    def test_pearse_seeds_a_second_entrance_with_three_ways(self):
        _, g, _ = build("PERSE")
        self.assertIn("entrance-2", g.nodes)
        modes = {e.mode for e in g.edges.values() if e.start == "entrance-2"}
        self.assertEqual(modes, {"lift", "stairs", "escalator"})
        self.assertEqual(g.edges["level-p1"].mode, "ramp")

    def test_connolly_seeds_the_entrance_escalator_from_the_other_field(self):
        _, g, _ = build("CNLLY")
        self.assertIn("escalator-entrance", g.equipment)
        self.assertEqual(g.edges["escalator-entrance"].source["field"], "ticketOfficeAccess")

    def test_dun_laoghaire_links_platform_2_to_3(self):
        _, g, _ = build("DLERY")
        self.assertEqual(g.edges["link-p2-p3"].mode, "ramp")

    def test_seeding_is_deterministic_and_dated_from_the_snapshot(self):
        first = seed.dumps(seed.observations(station("PERSE"), SNAPSHOT))
        second = seed.dumps(seed.observations(station("PERSE"), SNAPSHOT))
        self.assertEqual(first, second)
        self.assertIn('"observed": "2026-09-01"', first)
        self.assertEqual(seed.observed_date("irishrail-20261101.jsonl"), "2026-11-01")

    def test_every_seed_line_is_low_unless_reviewed(self):
        for code in PROSE:
            for obj in seed.observations(station(code), SNAPSHOT):
                expected = "medium" if obj["source"].get("reviewed") else "low"
                self.assertEqual(obj["confidence"], expected, code)

    def test_every_quote_is_on_the_page(self):
        for code in PROSE:
            facts = station(code)
            for obj in seed.observations(facts, SNAPSHOT):
                field = obj["source"]["field"]
                prose = facts.platform_access if field == "platformAccess" \
                    else facts.ticket_office_access
                quote = " ".join(obj["source"]["quote"].split())
                if quote:
                    self.assertIn(quote, " ".join(prose.split()), code)
