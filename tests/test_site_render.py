"""The emitted site: the files, the payload split, and the static pages."""

from __future__ import annotations

import json
import re
import unittest
from datetime import datetime, timedelta, timezone

from lift_site import model, render
from tests.test_site_model import NOW, T0, SiteModelCase, escalator, lift


def _data(site_dir):
    text = (site_dir / "data.js").read_text(encoding="utf-8")
    return json.loads(text.split("= ", 1)[1].rstrip(";\n"))


class TestWrite(SiteModelCase):
    def setUp(self):
        super().setUp()
        self.poll(T0, [lift(), escalator(), lift(station="Rush and Lusk", code="RLUSK")])
        self.poll(T0 + timedelta(hours=1), [lift(), escalator()])
        self.poll(T0 + timedelta(days=1), [lift(planned=True, station="Bray", code="BRAY")])
        outages = self.load()
        self.site = self.dir / "site"
        self.data = render.write(self.site, outages, NOW, self.until)

    def test_the_files_a_reader_and_a_crawler_expect(self):
        for name in ("index.html", "data.js", "sitemap.xml", "robots.txt"):
            self.assertTrue((self.site / name).exists(), name)
        for code in self.data["stations"]:
            self.assertTrue((self.site / "h" / f"{code}.js").exists(), code)
            self.assertTrue((self.site / "s" / f"{self.data['slugs'][code]}.html").exists(), code)

    def test_data_js_is_what_build_produced(self):
        self.assertEqual(_data(self.site), json.loads(json.dumps(self.data)))
        d = _data(self.site)
        self.assertEqual(d["months"], ["2026-08"])
        self.assertEqual(sorted(d["stations"]), ["ATHY", "BRAY", "CNLLY", "RLUSK"])
        self.assertEqual(d["current"], {"stations": 1, "lifts": 1, "escalators": 0})
        # Only station-months with a listing carry a bar; quiet ones use blank.
        self.assertIn("2026-08", d["stats"]["ATHY"])
        self.assertEqual(len(d["blank"]["2026-08"]), 31)

    def test_a_shard_carries_every_outage_at_the_station_and_no_other(self):
        text = (self.site / "h" / "ATHY.js").read_text(encoding="utf-8")
        shard = json.loads(text.split("= ", 1)[1].rstrip(";\n"))
        self.assertEqual([k[1] for k in shard["2026-08"]], ["lift"])
        text = (self.site / "h" / "CNLLY.js").read_text(encoding="utf-8")
        shard = json.loads(text.split("= ", 1)[1].rstrip(";\n"))
        self.assertEqual([k[1] for k in shard["2026-08"]], ["escalator"])

    def test_the_static_page_carries_the_station_its_months_and_its_cases(self):
        page = (self.site / "s" / "rush-and-lusk.html").read_text(encoding="utf-8")
        self.assertIn("<h1>Rush and Lusk</h1>", page)
        self.assertIn("August 2026", page)
        self.assertIn('class="case"', page)
        self.assertIn("no longer listed", page)
        self.assertIn(f'{render.BASE_URL}/s/rush-and-lusk.html', page)
        # The nav links every other station and not itself.
        self.assertIn('href="athy.html"', page)
        self.assertNotIn('href="rush-and-lusk.html"', page)

    def test_the_static_page_shows_both_clocks(self):
        page = (self.site / "s" / "athy.html").read_text(encoding="utf-8")
        self.assertIn("listed when collection began", page)
        self.assertIn("Irish Rail&#x27;s notice dates it from 1 Aug 2026, 09:00", page)
        self.assertIn("before it was listed", page)

    def test_sitemap_lists_the_front_page_and_every_station(self):
        sm = (self.site / "sitemap.xml").read_text(encoding="utf-8")
        locs = re.findall(r"<loc>([^<]+)</loc>", sm)
        self.assertEqual(locs[0], f"{render.BASE_URL}/")
        self.assertEqual(len(locs), 1 + len(self.data["stations"]))

    def test_initial_load_is_inside_the_budget(self):
        total, report = render.size_report(self.site)
        self.assertLess(total, render.BUDGET_BYTES)
        self.assertIn("initial load", report)

    def test_index_html_is_the_template_with_its_canonical_filled(self):
        page = (self.site / "index.html").read_text(encoding="utf-8")
        self.assertIn(f'<link rel="canonical" href="{render.BASE_URL}/">', page)
        self.assertNotIn("<!--CANONICAL-->", page)


class TestStaleness(SiteModelCase):
    def test_a_build_long_after_the_last_poll_says_so(self):
        self.poll(T0, [lift()])
        outages = self.load(now=T0 + timedelta(days=3))
        data, _, _ = render.build(outages, T0 + timedelta(days=3), self.until)
        self.assertTrue(data["stale"])
        page = render.station_page("ATHY", data, render.shard(outages, data["months"], self.until))
        self.assertIn("collection has stopped", page)

    def test_a_fresh_build_does_not(self):
        self.poll(T0, [lift()])
        outages = self.load(now=T0 + timedelta(hours=3))
        data, _, _ = render.build(outages, T0 + timedelta(hours=3), self.until)
        self.assertFalse(data["stale"])


class TestSlugs(unittest.TestCase):
    def test_names_become_paths_and_collisions_get_the_code(self):
        self.assertEqual(
            render.station_slugs(
                {"A": "Rush and Lusk", "B": "Dún Laoghaire", "C": "Rush and Lusk"}
            ),
            {"A": "rush-and-lusk", "B": "dun-laoghaire", "C": "rush-and-lusk-c"},
        )


class TestWords(unittest.TestCase):
    def test_durations_read_at_the_right_scale(self):
        self.assertEqual(render._hours(0.5), "30 min")
        self.assertEqual(render._hours(9.96), "10.0 h")
        self.assertEqual(render._hours(23), "23 h")
        self.assertEqual(render._hours(24 * 3), "3 days")
        self.assertEqual(render._hours(24 * 100), "3.3 months")

    def test_the_summary_keeps_the_two_clocks_apart(self):
        bits = render.summary_bits(
            "2026-08-13T11:30", "2026-08-14T10:02", 0, "2026-05-05T00:00", "2026-12-31T23:59", 100
        )
        self.assertEqual(bits[0], "first listed 13 Aug 2026, 11:30")
        self.assertEqual(bits[1], "no longer listed 14 Aug 2026, 10:02")
        self.assertIn("dates it from 5 May 2026, 00:00 — 3.3 months before it was listed", bits[2])
        self.assertEqual(bits[3], "listed end 31 Dec 2026, 23:59")

    def test_a_start_on_the_listing_day_is_not_before_it(self):
        bits = render.summary_bits(
            "2026-08-13T11:30", "2026-08-14T10:02", 1, "2026-08-13T09:00", None
        )
        self.assertEqual(bits[1], "still listed at the last poll")
        self.assertNotIn("before it was listed", bits[2])
        self.assertEqual(len(bits), 3)


class TestMonths(unittest.TestCase):
    def test_month_list_runs_from_collection_start_to_now(self):
        self.assertEqual(
            model.month_list(model.COLLECTION_START, datetime(2026, 10, 2, tzinfo=timezone.utc)),
            ["2026-08", "2026-09", "2026-10"],
        )

    def test_a_month_arrives_at_its_first_midnight_not_at_the_start_time(self):
        # COLLECTION_START is 21:30, and the Pages build runs at 05:40. Carrying
        # that time of day forward hid the new month from the first build of
        # every month, and with it every notice first listed that morning.
        build_clock = datetime(2026, 9, 1, 5, 40, tzinfo=timezone.utc)
        self.assertEqual(
            model.month_list(model.COLLECTION_START, build_clock), ["2026-08", "2026-09"]
        )


if __name__ == "__main__":
    unittest.main()
