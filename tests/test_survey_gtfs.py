"""The export is GTFS-Pathways shaped and reads back with the csv module."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from lift_access import gtfs, snapshot
from tests.test_access_model import station
from tests.test_survey_graph import build, line


class Export(unittest.TestCase):
    def setUp(self):
        self.g, _ = build([
            line({"type": "level", "id": "street", "index": 0, "name": "Street"}),
            line({"type": "edge", "id": "back", "mode": "unsurveyed", "from": "side",
                  "to": "hall"}),
            line({"type": "edge", "id": "barrier", "mode": "gate", "gate": "ticket-barrier",
                  "from": "hall", "to": "p1"}),
        ])

    def test_location_types(self):
        rows = {r["stop_id"]: r for r in gtfs.stop_rows(self.g)}
        self.assertEqual(rows["TOY"]["location_type"], 1)
        self.assertEqual(rows["TOY:p1"]["location_type"], 0)
        self.assertEqual(rows["TOY:main"]["location_type"], 2)
        self.assertEqual(rows["TOY:hall"]["location_type"], 3)
        self.assertEqual(rows["TOY:p1"]["parent_station"], "TOY")
        self.assertEqual(rows["TOY:p1"]["platform_code"], "1")

    def test_wheelchair_boarding_comes_from_reachability(self):
        g, _ = build([line({"type": "retract", "id": "to-p1", "of": "edge"})])
        rows = {r["stop_id"]: r for r in gtfs.stop_rows(g)}
        self.assertEqual(rows["TOY:p1"]["wheelchair_boarding"], 2)
        self.assertEqual(rows["TOY:p2"]["wheelchair_boarding"], 1)

    def test_pathway_modes(self):
        rows = {r["pathway_id"]: r for r in gtfs.pathway_rows(self.g)}
        self.assertEqual(rows["TOY:way-in"]["pathway_mode"], 1)
        self.assertEqual(rows["TOY:up-stairs"]["pathway_mode"], 2)
        self.assertEqual(rows["TOY:up-stairs"]["stair_count"], 24)
        self.assertEqual(rows["TOY:up-esc"]["pathway_mode"], 4)
        self.assertEqual(rows["TOY:up"]["pathway_mode"], 5)
        self.assertEqual(rows["TOY:barrier"]["pathway_mode"], 6)
        self.assertEqual(rows["TOY:side-gate"]["pathway_mode"], 1)
        self.assertEqual(rows["TOY:ramp-p3"]["max_slope"], 8)
        self.assertNotIn("TOY:back", rows)

    def test_levels_only_when_recorded(self):
        self.assertEqual(gtfs.level_rows(self.g)[0]["level_index"], 0)
        plain, _ = build()
        self.assertEqual(gtfs.level_rows(plain), [])

    def test_the_files_read_back(self):
        facts = snapshot.Facts({"TOY": station("ATHY")._replace(code="TOY", latitude="53.0",
                                                                longitude="-7.0")})
        with tempfile.TemporaryDirectory() as tmp:
            written = gtfs.export([self.g], facts, tmp)
            self.assertEqual([p.name for p in written], ["stops.txt", "pathways.txt", "levels.txt"])
            with open(Path(tmp) / "stops.txt", newline="", encoding="utf-8") as handle:
                stops = list(csv.DictReader(handle))
            self.assertEqual(stops[0]["stop_lat"], "53.0")
            self.assertEqual(len(stops), 1 + len(self.g.nodes))
            with open(Path(tmp) / "pathways.txt", newline="", encoding="utf-8") as handle:
                self.assertEqual(len(list(csv.DictReader(handle))), len(self.g.edges) - 1)
            plain, _ = build()
            written = gtfs.export([plain], facts, tmp)
            self.assertEqual([p.name for p in written], ["stops.txt", "pathways.txt"])
