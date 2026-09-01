"""The emitted site: the files, the payload split, and the static pages."""

from __future__ import annotations

import html as html_mod
import json
import re
import unittest
import urllib.parse
from datetime import UTC, datetime, timedelta
from pathlib import Path

from lift_access import model as access_model
from lift_access import snapshot
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
        bray = lift(planned=True, station="Bray", code="BRAY")
        self.poll(T0 + timedelta(days=1), [bray])
        self.poll(T0 + timedelta(days=1, hours=1), [bray])  # second miss closes the rest
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
        # [cells, faults, planned, ongoing, avail] and nothing else at a
        # station with no escalator notice: every byte is in the initial load.
        self.assertEqual(len(d["stats"]["ATHY"]["2026-08"]), 5)
        # the model's own table, not a second copy of it: the app derives its
        # letter from this, so a band that drifted here would grade differently
        # from the static pages
        self.assertEqual(d["bands"], [list(b) for b in model.GRADE_BANDS])

    def test_only_a_station_with_an_escalator_notice_carries_a_second_bar(self):
        d = _data(self.site)
        esc = d["stats"]["CNLLY"]["2026-08"]
        self.assertEqual(len(esc), 6)
        self.assertEqual(len(esc[5]), 31)
        # Connolly's notice is the escalator's, so the lift bar stays clear -
        # but the grade counts both kinds, so it is not a clean 100%.
        self.assertEqual(set(esc[0]) - set("89"), {"0"})
        self.assertLess(esc[4], 100)

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
        self.assertIn('<span class="gradechip g-', page)
        self.assertIn("% of days available", page)
        self.assertIn("August 2026", page)
        self.assertIn('class="case"', page)
        self.assertIn("no longer listed", page)
        self.assertIn(f'{render.BASE_URL}/s/rush-and-lusk.html', page)

    def test_every_bar_says_which_kind_it_carries(self):
        """Adjacency is the assertion. The legend carries both glyphs on every
        page, so a bare "the page contains kind-lift" passes with the gutter
        taken out of the bars entirely - it is the key it finds, not a bar."""
        page = (self.site / "s" / "dublin-connolly.html").read_text(encoding="utf-8")
        self.assertIn('></i>Lifts</span><div class="bar tall"', page)
        self.assertIn('></i>Escalators</span><div class="bar tall"', page)
        self.assertIn("escalator out of service", page)
        # a station with no escalator notice says "lift" rather than nothing,
        # and still does not claim an escalator the feed has never mentioned
        athy = (self.site / "s" / "athy.html").read_text(encoding="utf-8")
        self.assertIn('></i>Lifts</span><div class="bar tall"', athy)
        self.assertNotIn("Escalators</span>", athy)
        self.assertNotIn("Escalators in", athy)  # no escalator strip, only the key

    def test_the_overview_bar_carries_its_glyph_too(self):
        """The short bar has no static page to appear on - renderOverview builds
        it in JS - so the only place its markup can be checked is here."""
        row = render._bars("0" * 31, None, "2026-08", ())
        self.assertIn(
            '<i class="kind kind-lift" aria-hidden="true" title="Lift"></i><div class="bar"',
            row,
        )
        self.assertNotIn("kind-escalator", row)
        pair = render._bars("0" * 31, "1" * 31, "2026-08", ())
        self.assertIn(
            '<i class="kind kind-escalator" aria-hidden="true" title="Escalator"></i>'
            '<div class="bar"',
            pair,
        )

    def test_a_single_bar_reserves_the_same_gutter_as_a_pair(self):
        """The 64px text label tried in August shortened one row's bar and put
        its days out of line with the rest. A cell every bar carries cannot."""
        athy = (self.site / "s" / "athy.html").read_text(encoding="utf-8")
        self.assertIn('<div class="bars labelled">', athy)
        # only the pair splits the height; a lone bar keeps the whole of it
        self.assertNotIn('class="bars labelled pair"', athy)
        connolly = (self.site / "s" / "dublin-connolly.html").read_text(encoding="utf-8")
        self.assertIn('<div class="bars labelled pair">', connolly)

    def test_the_kind_key_is_not_the_day_key(self):
        """Colour says what was listed, shape says which kind. Two keys on one
        line, and neither may start explaining the other."""
        self.assertIn("kind-lift", render.KIND_SPANS)
        self.assertIn("kind-escalator", render.KIND_SPANS)
        self.assertIn(render.KIND_SPANS, render.LEGEND_HTML)
        self.assertIn(render.LEGEND_SPANS, render.LEGEND_HTML)

    def test_the_static_page_drops_the_listed_end_once_the_notice_is_down(self):
        # Bray's notice is still up at the last poll; Athy's came down with the
        # same placeholder end date on it.
        self.assertIn("listed end", (self.site / "s" / "bray.html").read_text(encoding="utf-8"))
        page = (self.site / "s" / "athy.html").read_text(encoding="utf-8")
        self.assertIn("no longer listed", page)
        self.assertNotIn("listed end", page)

    def test_a_station_page_links_what_is_out_now_and_the_full_list_once(self):
        """The card used to link every other station from every page: the same
        links in the same order, growing with the square of the station count.
        Bray is the only notice still up at the last poll, so it is the only
        station Rush and Lusk links - and the index carries the rest."""
        page = (self.site / "s" / "rush-and-lusk.html").read_text(encoding="utf-8")
        self.assertIn('href="bray.html"', page)
        self.assertNotIn('href="athy.html"', page)
        self.assertNotIn('href="rush-and-lusk.html"', page)
        self.assertIn('href="../index.html"', page)

    def test_a_page_with_nothing_else_listed_says_so(self):
        page = (self.site / "s" / "bray.html").read_text(encoding="utf-8")
        self.assertIn("Nothing else was out when we last checked.", page)
        self.assertNotIn('href="bray.html"', page)

    def test_the_index_is_the_one_page_that_links_every_station(self):
        """Without it a reader with no JavaScript, and a crawler that does not
        run it, has no path to a station page at all: the overview's own list is
        built from data.js."""
        index = (self.site / "index.html").read_text(encoding="utf-8")
        for code, name in self.data["stations"].items():
            with self.subTest(code=code):
                self.assertIn(f'href="s/{self.data["slugs"][code]}.html">{name}</a>', index)
        self.assertIn("not every station with a lift", index)
        self.assertIn("since 8 August 2026", index)

    def test_the_static_page_says_what_a_bar_and_a_chip_mean(self):
        """A month of empty `<i>`s and a bare letter convey nothing to a screen
        reader. Each bar is one image with one sentence; the chip says what it
        grades, and the heading's says which month, because the page has all of
        them."""
        page = (self.site / "s" / "athy.html").read_text(encoding="utf-8")
        self.assertIn('role="img" aria-label="Lifts in August 2026: listed on 2 of', page)
        self.assertIn('aria-label="Grade F for August 2026"', page)
        self.assertIn("graded on August 2026", page)
        conn = (self.site / "s" / "dublin-connolly.html").read_text(encoding="utf-8")
        self.assertIn("Escalators in August 2026: listed on", conn)
        # Connolly's lifts were never listed, and the bar has to say so rather
        # than borrow the escalator's news
        self.assertIn("Lifts in August 2026: nothing listed on", conn)

    def test_a_station_page_can_be_shared(self):
        page = (self.site / "s" / "athy.html").read_text(encoding="utf-8")
        self.assertIn('<meta property="og:title" content="Lift outages at Athy station">', page)
        self.assertIn(f'<meta property="og:url" content="{render.BASE_URL}/s/athy.html">', page)
        self.assertIn('<meta property="og:description" content="Lift (elevator)', page)

    def test_the_feed_is_named_the_way_the_footer_names_it(self):
        page = (self.site / "s" / "athy.html").read_text(encoding="utf-8")
        self.assertIn("service message feed", page)
        self.assertNotIn("service-message feed", page)

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


class TestSkewedClocks(SiteModelCase):
    def test_the_horizons_month_is_on_the_page_even_if_the_clock_lags(self):
        """The months come from the build clock and the horizon from the
        collector's. A horizon in a month the list lacks would drop that
        month's outages from the shards, the stats and the headline."""
        self.poll(T0, [lift()])
        outages = self.load()
        # the collector's clock five days ahead of the builder's, over a month
        # end: months run from the collection month, so the one that can go
        # missing is the horizon's, not the build clock's
        now = datetime(2026, 8, 28, 12, 0, tzinfo=UTC)
        until = datetime(2026, 9, 2, 12, 0, tzinfo=UTC)
        data, _, months = render.build(outages, now, until)
        self.assertEqual(months, ["2026-08", "2026-09"])
        self.assertEqual(data["observed_month"], "2026-09")
        self.assertIn("2026-09", data["blank"])
        self.assertIn("2026-09", data["national"])
        self.assertEqual(model.month_list(model.COLLECTION_START, now), ["2026-08"])


class TestStaleness(SiteModelCase):
    def test_a_build_long_after_the_last_poll_says_so(self):
        self.poll(T0, [lift()])
        outages = self.load(now=T0 + timedelta(days=3))
        data, _, _ = render.build(outages, T0 + timedelta(days=3), self.until)
        self.assertTrue(data["stale"])
        page = render.station_page("ATHY", data, render.shard(outages, data["months"], self.until))
        self.assertIn(f'Data to <span class="stale">{data["observed"]}</span>', page)

    def test_a_fresh_build_does_not(self):
        self.poll(T0, [lift()])
        outages = self.load(now=T0 + timedelta(hours=3))
        data, _, _ = render.build(outages, T0 + timedelta(hours=3), self.until)
        self.assertFalse(data["stale"])
        page = render.station_page("ATHY", data, render.shard(outages, data["months"], self.until))
        self.assertIn(f'Data to {data["observed"]}<', page)
        self.assertNotIn('class="stale"', page)


class TestSlugs(unittest.TestCase):
    def test_names_become_paths_and_collisions_get_the_code(self):
        self.assertEqual(
            render.station_slugs(
                {"A": "Rush and Lusk", "B": "Dún Laoghaire", "C": "Rush and Lusk"}
            ),
            {"A": "rush-and-lusk", "B": "dun-laoghaire", "C": "rush-and-lusk-c"},
        )


class TestMonthSections(SiteModelCase):
    """A station's page carries every month since collection began. The months
    it had a notice in are cards; the rest are lines."""

    def setUp(self):
        super().setUp()
        self.poll(T0, [lift()])
        self.drop(T0 + timedelta(hours=1))
        october = datetime(2026, 10, 5, 10, 0, tzinfo=UTC)
        # a notice of its own, not August's coming back: a reopened notice
        # still publishes its gap as listed (notes/site.md, Open)
        self.poll(october, [lift(start="2026-10-01T09:00:00")])
        self.drop(october + timedelta(days=1))
        self.now = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
        outages = self.load(now=self.now)
        self.site = self.dir / "site"
        self.data = render.write(self.site, outages, self.now, self.until)
        self.page = (self.site / "s" / "athy.html").read_text(encoding="utf-8")

    def test_a_month_with_a_notice_is_a_card_and_the_rest_are_lines(self):
        self.assertIn('<div class="card" id="ym-2026-10">', self.page)
        self.assertIn('<div class="card" id="ym-2026-08">', self.page)
        self.assertNotIn('id="ym-2026-09"', self.page)
        self.assertIn("September 2026 · nothing listed, 30 days watched", self.page)
        # November is past the horizon: nobody watched it, which is not the
        # same as nothing being listed in it.
        self.assertIn("November 2026 · no data collected", self.page)

    def test_the_months_with_cards_are_linked_from_the_top(self):
        strip = re.search(r'<div class="months jumps">(.*?)</div>', self.page, re.S).group(1)
        self.assertEqual(
            re.findall(r'href="#ym-([\d-]+)"', strip), ["2026-10", "2026-08"]
        )

    def test_one_card_needs_no_strip(self):
        page = render.station_page(
            "ATHY", self.data, {"2026-08": []}, ()
        )
        self.assertNotIn("months jumps", page)


class TestMonthSectionRules(unittest.TestCase):
    BLANK = {
        "2026-08": "0" * 31, "2026-09": "0" * 30,
        "2026-10": "8" * 31, "2026-11": "8" * 30, "2026-12": "0" * 31,
    }

    def sections(self, loud):
        return render.month_sections(
            list(self.BLANK), {ym: [1] for ym in loud}, self.BLANK
        )

    def test_consecutive_quiet_months_fold_into_one_run(self):
        self.assertEqual(
            self.sections(["2026-12"]),
            [["quiet", ["2026-08", "2026-09"], 61],
             ["quiet", ["2026-10", "2026-11"], 0],
             ["card", "2026-12", 0]],
        )

    def test_a_card_breaks_a_run_and_so_does_the_data_running_out(self):
        self.assertEqual(
            self.sections(["2026-09"]),
            [["quiet", ["2026-08"], 31],
             ["card", "2026-09", 0],
             ["quiet", ["2026-10", "2026-11"], 0],
             ["quiet", ["2026-12"], 31]],
        )

    def test_a_run_reads_from_its_oldest_month_to_its_newest(self):
        self.assertEqual(
            render._quiet_row(["2026-11", "2026-10"], 0),
            '<div class="quiet">October 2026 to November 2026 · no data collected</div>',
        )
        self.assertIn("August 2026 · nothing listed, 1 day watched",
                      render._quiet_row(["2026-08"], 1))


class TestBarLabel(unittest.TestCase):
    """The sentence a bar reads out. Mirrored line for line by site.html's
    barLabel(), which is why the wording lives in one function here."""

    def test_it_counts_the_days_watched_and_the_days_listed(self):
        self.assertEqual(
            render._bar_label("8888888115000000000000000009999", "2026-08", "lift"),
            "Lifts in August 2026: listed on 3 of 20 days watched",
        )

    def test_a_quiet_month_says_so_rather_than_saying_nothing(self):
        self.assertEqual(
            render._bar_label("0" * 31, "2026-08", "escalator"),
            "Escalators in August 2026: nothing listed on 31 days watched",
        )

    def test_a_month_nobody_watched_is_not_a_month_with_nothing_listed(self):
        self.assertEqual(
            render._bar_label("8" * 31, "2026-08", "lift"),
            "Lifts in August 2026: no data collected",
        )

    def test_one_day_is_not_one_days(self):
        self.assertIn("on 1 day watched", render._bar_label("0" + "8" * 30, "2026-08", "lift"))


class TestLegend(unittest.TestCase):
    def test_each_key_carries_its_own_name(self):
        """The kind key and the day key were divided by a 1px rule and nothing
        else, which divides them for an eye only: a screen reader heard one run
        of seven items and was told the kinds were day-cell colours."""
        for name in ("Which kind each bar carries", "What a day's colour means"):
            self.assertIn(f'role="group" aria-label="{name}"', render.LEGEND_HTML)
        self.assertEqual(2, render.LEGEND_HTML.count('class="keys"'))

    def test_the_grade_key_says_what_the_model_grades(self):
        self.assertEqual(
            [letter for letter, _ in render.GRADE_LABELS],
            [letter for _, letter in model.GRADE_BANDS],
        )
        for letter, _ in render.GRADE_LABELS:
            # the letter, not a bare swatch: the chip is how a reader reads a
            # grade, and a colour key to a colour nothing else uses said nothing
            self.assertIn(f'class="gradechip g-{letter}"', render.GRADE_SPANS)
            self.assertIn(f">{letter}</span>", render.GRADE_SPANS)

    def test_the_grade_key_does_not_promise_an_empty_bar(self):
        """A is 100% of the days that counted. A planned-works notice inside its
        grace is on the bar and off the total, so "no days listed" was a claim
        the page contradicts - Pearse grades A over six planned cells."""
        self.assertNotIn("no days listed", render.GRADE_SPANS)
        self.assertIn("100% available", render.GRADE_SPANS)

    def test_every_day_code_the_bars_use_has_a_caption(self):
        self.assertEqual(
            set(render._day_labels("lift")),
            {
                str(c)
                for c in (
                    model.DAY_CLEAR, model.DAY_OUT, model.DAY_PLANNED,
                    model.DAY_PLANNED_LONG, model.DAY_NO_DATA, model.DAY_FUTURE,
                )
            },
        )

    def test_the_two_planned_codes_are_not_the_same_colour(self):
        """Works inside their grace are off the total and works past it are on
        it, in full. One blue for both had Midleton at 0% and Pearse at 100%
        with the same shade across both bars."""
        css = Path(render.SITE_CSS).read_text(encoding="utf-8")
        fills = {}
        for cls in ("b1", "b5", "b6"):
            self.assertIn(f'<i class="{cls}">', render.LEGEND_SPANS)
            found = re.search(rf"\.bar i\.{cls},[^{{]*\{{\s*background:\s*([^;]+);", css)
            self.assertIsNotNone(found, f"{cls} has no fill in site.css")
            fills.setdefault(found.group(1).strip(), []).append(cls)
        self.assertEqual(sorted(fills.values()), [["b1"], ["b5"], ["b6"]])

    def test_the_day_key_no_longer_names_a_kind(self):
        # The kind is the bar, not the colour, so no swatch may claim one.
        self.assertNotIn("lift", render.LEGEND_SPANS)
        self.assertNotIn("escalator", render.LEGEND_SPANS)


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
        self.assertIn("dates it from 5 May 2026, 00:00 - 3.3 months before it was listed", bits[2])
        self.assertEqual(bits[3], "listed end 31 Dec 2026, 23:59")

    def test_a_start_on_the_listing_day_is_not_before_it(self):
        bits = render.summary_bits(
            "2026-08-13T11:30", "2026-08-14T10:02", 1, "2026-08-13T09:00", None
        )
        self.assertEqual(bits[1], "still listed when we last checked")
        self.assertNotIn("before it was listed", bits[2])
        self.assertEqual(len(bits), 3)


class TestMonths(unittest.TestCase):
    def test_month_list_runs_from_collection_start_to_now(self):
        self.assertEqual(
            model.month_list(model.COLLECTION_START, datetime(2026, 10, 2, tzinfo=UTC)),
            ["2026-08", "2026-09", "2026-10"],
        )

    def test_a_month_arrives_at_its_first_midnight_not_at_the_start_time(self):
        # COLLECTION_START is 21:30, and the Pages build runs at 05:40. Carrying
        # that time of day forward hid the new month from the first build of
        # every month, and with it every notice first listed that morning.
        build_clock = datetime(2026, 9, 1, 5, 40, tzinfo=UTC)
        self.assertEqual(
            model.month_list(model.COLLECTION_START, build_clock), ["2026-08", "2026-09"]
        )


if __name__ == "__main__":
    unittest.main()


class TestStepFreeChip(SiteModelCase):
    """The chip for the two stations with a lift-independent step-free route.

    Neither Raheny nor Cork has ever had a notice in the real corpus, so this is
    the only thing exercising the chip. It is here rather than nowhere because a
    marker that has never rendered is a marker nobody has checked.
    """

    def _facts(self, code, name, prose):
        lift_platforms, claims, denies = access_model.read_platform_access(prose)
        station = access_model.Station(
            code=code, name=name, slug=code.lower(), latitude=None, longitude=None,
            platform_access=access_model.plain(prose), ticket_office_access="",
            lift_platforms=lift_platforms,
            claims_lift=claims, denies_lift=denies,
        )
        return snapshot.Facts({code: station})

    def _build(self, code, name, prose):
        self.poll(T0, [lift(station=name, code=code)])
        outages = self.load()
        site = self.dir / "site"
        facts = self._facts(code, name, prose)
        data = render.write(site, outages, NOW, self.until, facts)
        page = (site / "s" / f"{data['slugs'][code]}.html").read_text(encoding="utf-8")
        return data, page

    def test_raheny_is_chipped_and_says_which_line_earned_it(self):
        data, page = self._build(
            "RAHNY",
            "Raheny",
            "<p>Lift or ramp to platform 1 (City Centre and Southbound)<br>"
            "Ramp to platform 2 (Northbound)</p>",
        )
        self.assertEqual(data["stepfree"], ["RAHNY"])
        self.assertIn("sfchip", page)
        self.assertIn(render.STEP_FREE_CHIP, page)
        self.assertIn("Lift or ramp to platform 1", page)

    def test_a_station_with_no_reviewed_entry_is_not_chipped(self):
        data, page = self._build(
            "ATHY", "Athy", "<p>Level to platform 1<br>Lift to platform 2</p>"
        )
        self.assertEqual(data["stepfree"], [])
        self.assertNotIn("sfchip", page.split("</style>", 1)[-1])

    def test_a_station_missing_from_the_snapshot_is_not_chipped(self):
        # The chip asserts something about prose. Without the station there is
        # no prose, and the page's own "Getting to the platforms" card is empty,
        # so the chip would be an unexplained accessibility claim.
        self.poll(T0, [lift(station="Raheny", code="RAHNY")])
        site = self.dir / "site"
        data = render.write(site, self.load(), NOW, self.until, snapshot.Facts({}))
        self.assertEqual(data["stepfree"], [])
        page = (site / "s" / f"{data['slugs']['RAHNY']}.html").read_text(encoding="utf-8")
        self.assertNotIn("sfchip", page.split("</style>", 1)[-1])

    def test_a_reworded_page_withdraws_the_chip_too(self):
        # The chip and the verdict ask the same question, so they cannot
        # disagree about whether the reviewed sentence is still there.
        self.poll(T0, [lift(station="Raheny", code="RAHNY")])
        facts = self._facts("RAHNY", "Raheny", "<p>Lift to platform 1</p>")
        site = self.dir / "site"
        data = render.write(site, self.load(), NOW, self.until, facts)
        self.assertEqual(data["stepfree"], [])

    def test_a_derived_claim_says_it_is_derived(self):
        # Nothing here is a survey. The prose is hand-written and this project
        # has already found a typo, a self-contradiction and an omitted
        # escalator in it, so the page says so where the claims are.
        _, page = self._build("ATHY", "Athy", "<p>Level to platform 1<br>Lift to platform 2</p>")
        self.assertIn("not a survey", page)
        self.assertIn("has been wrong before", page)

    def test_a_reader_who_knows_better_is_asked_to_say_so(self):
        _, page = self._build("ATHY", "Athy", "<p>Level to platform 1<br>Lift to platform 2</p>")
        self.assertIn(render.CORRECTION_PROMPT, page)
        self.assertIn("issues/new?title=Station+access%3A+Athy", page)

    def test_the_permalink_in_the_report_points_at_the_real_page(self):
        # The site names pages from the notice's station name and the snapshot
        # has its own. Re-deriving the slug sent Clondalkin and Hazelhatch to
        # pages that do not exist.
        data, page = self._build(
            "HZLCH", "Hazelhatch", "<p>Lift to platform 2</p>"
        )
        m = re.search(r'href="(https://github\.com/baz8080/lifts/issues/new[^"]*)"', page)
        self.assertIsNotNone(m)
        query = urllib.parse.parse_qs(
            urllib.parse.urlparse(html_mod.unescape(m.group(1))).query
        )
        self.assertEqual(query["title"], ["Station access: Hazelhatch"])
        self.assertIn(f"/s/{data['slugs']['HZLCH']}.html", query["body"][0])

    def test_the_app_only_caveats_stations_it_has_facts_for(self):
        # A global flag printed "worked out from Irish Rail's page" above "this
        # station is not in the station snapshot".
        data, _ = self._build("ATHY", "Athy", "<p>Lift to platform 2</p>")
        self.assertEqual(data["access"], ["ATHY"])
        markup = (Path(render.TEMPLATES) / "site.html").read_text(encoding="utf-8")
        self.assertIn("D.access.indexOf(code) >= 0", markup)

    def test_the_app_carries_the_caveat_too(self):
        # It renders verdicts without the card that holds their source.
        data, _ = self._build("ATHY", "Athy", "<p>Lift to platform 2</p>")
        self.assertEqual(data["access_caveat"], render.ACCESS_CAVEAT)
        markup = (Path(render.TEMPLATES) / "site.html").read_text(encoding="utf-8")
        self.assertIn("D.access_caveat", markup)

    def test_no_snapshot_means_no_caveat_because_there_is_no_claim(self):
        self.poll(T0, [lift()])
        data = render.write(self.dir / "site", self.load(), NOW, self.until)
        self.assertIsNone(data["access_caveat"])

    def test_the_chip_does_not_claim_the_station_is_accessible(self):
        # "Accessible station" is a far bigger claim than the reviewed list
        # makes, and the international access symbol would read as one.
        for text in (render.STEP_FREE_CHIP, render.STEP_FREE_TITLE):
            self.assertNotIn("accessible", text.lower())
            self.assertNotIn("♿", text)

    def test_the_two_renderers_use_the_same_words(self):
        markup = (Path(render.TEMPLATES) / "site.html").read_text(encoding="utf-8")
        self.assertIn(f'var STEP_FREE_CHIP = "{render.STEP_FREE_CHIP}"', markup)
        self.assertIn(f'var STEP_FREE_TITLE = "{render.STEP_FREE_TITLE}"', markup)

    def test_the_app_chips_the_row_and_the_detail_head(self):
        markup = (Path(render.TEMPLATES) / "site.html").read_text(encoding="utf-8")
        self.assertEqual(markup.count("stepFreeChip("), 3)  # definition, row, detail


class TestTheOtherPlatformNote(SiteModelCase):
    """The note travels inside the verdict sentence, so one build proves both
    the static page and the shard the app reads. Issue #31.
    """

    def _build(self):
        # Two polls: a notice first seen at the only poll sits on a zero-width
        # observed window and lands in no month's shard.
        item = lift(text="The lift at platform 2 is currently out of service.")
        self.poll(T0, [item])
        self.poll(T0 + timedelta(hours=1), [item])
        prose = "<p>Level to platform 1<br>Lift to platform 2</p>"
        lift_platforms, claims, denies = access_model.read_platform_access(prose)
        station = access_model.Station(
            code="ATHY", name="Athy", slug="athy", latitude=None, longitude=None,
            platform_access=access_model.plain(prose), ticket_office_access="",
            lift_platforms=lift_platforms, claims_lift=claims, denies_lift=denies,
        )
        site = self.dir / "site"
        data = render.write(site, self.load(), NOW, self.until, snapshot.Facts({"ATHY": station}))
        page = (site / "s" / f"{data['slugs']['ATHY']}.html").read_text(encoding="utf-8")
        shard = (site / "h" / "ATHY.js").read_text(encoding="utf-8")
        return page, json.loads(shard.split("= ", 1)[1].rstrip(";\n"))

    def test_the_page_and_the_shard_carry_the_same_sentence(self):
        note = 'Platform 1 needed no lift, so it kept step-free access: "Level to platform 1".'
        page, shard = self._build()
        self.assertIn("acc-lost", page)
        self.assertIn(html_mod.escape(note), page)
        records = next(iter(shard["2026-08"]))
        state, sentence = records[13]
        self.assertEqual(state, "lost")
        self.assertIn(note, sentence)
