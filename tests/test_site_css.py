"""The shared drill-down sub line, asserted to apply rather than to exist.

`.chead + .sub` styles the line under a station heading - here, the station code
and the data stamp on every `s/<slug>.html`. It lives in statusui's base.css and
reaches this repo only through the pin in `uv.lock`.

This repo carried a byte-identical copy in its own site.css until 2026-08-26,
and when the rule moved upstream that copy had to be kept back for one commit,
because `uv.lock` can only track statusui's `main`. Dropping both at once would
have left the line unstyled on the deployed site with every test still green:
nothing asserted a rule *applied*, only that files said what they said.

Three things make a rule apply, and a build can check all three without a
browser: the page renders an element for it to match, the rule is in the
stylesheet that page inlines, and nothing in the cascade beats it. base.css also
carries `header .sub`, which sets the same two properties, so the third is a
real question rather than a formality.
"""

from __future__ import annotations

import re
import unittest
from datetime import timedelta
from pathlib import Path

import statusui

from lift_site import render
from tests.test_site_model import NOW, T0, SiteModelCase, escalator, lift

SHARED = {"color": "var(--muted)", "font-size": "12.5px", "margin-bottom": "16px"}


def _stylesheet(page):
    """What the page inlines: assemble() puts base.css and site.css in a <style>
    block, so this is the whole stylesheet a browser would apply."""
    css = "\n".join(re.findall(r"<style>(.*?)</style>", page, re.S))
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _specificity(sel):
    return (
        len(re.findall(r"#[\w-]+", sel)),
        len(re.findall(r"\.[\w-]+|\[[^\]]*\]|:(?!:)[\w-]+", sel)),
        len(re.findall(r"(?:^|[\s>+~])([a-zA-Z][\w-]*)", sel)),
    )


def _winner(css, prop):
    """The value the cascade leaves standing on a `.sub`, or None if nothing
    sets it.

    Only a selector's subject is read; an ancestor or sibling part is assumed to
    match, which can only make this stricter than the browser. A rule inside an
    @media block is counted as competing whatever its condition, for the same
    reason - neither file puts a `.sub` rule in one today.
    """
    rules = []
    for order, (prelude, body) in enumerate(re.findall(r"([^{}]+)\{([^{}]*)\}", css)):
        decls = re.findall(rf"(?:^|;)\s*{re.escape(prop)}\s*:\s*([^;]+)", body)
        if not decls:
            continue
        for sel in (s.strip() for s in prelude.split(",")):
            if re.split(r"[\s>+~]+", sel)[-1] == ".sub":
                rules.append((_specificity(sel), order, decls[-1].strip()))
    return max(rules)[2] if rules else None


class StationPageCase(SiteModelCase):
    """Built through the same path a real run uses, so the page under test is
    the page that ships."""

    notices = (lift(),)

    def setUp(self):
        super().setUp()
        # twice: with one poll the window is a single instant and nothing is
        # listed inside it, so the page would carry no bars to test
        self.poll(T0, list(self.notices))
        self.poll(T0 + timedelta(hours=1), list(self.notices))
        outages = self.load()
        site = self.dir / "site"
        data = render.write(site, outages, NOW, self.until)
        code = next(iter(data["stations"]))
        self.page = (site / "s" / f"{data['slugs'][code]}.html").read_text(encoding="utf-8")


class SharedSubLineCase(StationPageCase):

    def test_the_page_renders_an_element_the_rule_can_match(self):
        """A rule with nothing to match is a rule that does not apply. The
        lookahead keeps the closing tag the `.chead`'s own, so a nested div
        could not fake the adjacency."""
        self.assertRegex(
            self.page, r'<div class="chead">(?:(?!</?div).)*</div>\s*<div class="sub"'
        )

    def test_the_shared_values_win_on_that_page(self):
        css = _stylesheet(self.page)
        for prop, expected in SHARED.items():
            with self.subTest(prop=prop):
                self.assertEqual(
                    _winner(css, prop),
                    expected,
                    f"{prop} on the station page's sub line is not the shared value;"
                    " the rule from statusui either never arrived or lost the cascade",
                )

    def test_the_rule_is_upstream_and_has_not_been_copied_back(self):
        """Three byte-identical copies across three repos is what moving it to
        statusui existed to end."""
        self.assertIn(".chead + .sub", statusui.base_css())
        self.assertNotIn(".chead + .sub", Path(render.SITE_CSS).read_text(encoding="utf-8"))


class PairedBarsCase(StationPageCase):
    """A station with two strips, and the reflow that nearly hid one.

    statusui's 640 px rules move `.bar` onto its own line by grid area. Inside
    this site's `.bars` wrapper that names an implicit line in the wrapper's own
    grid, so both strips land on it and the escalator is painted over the lift -
    on a phone only, which is where most readers are.
    """

    # one station, both kinds, so the page under test carries the pair
    notices = (lift(station="Dublin Pearse", code="PERSE"),
               escalator(station="Dublin Pearse", code="PERSE"))

    def test_the_page_renders_the_pair_the_rule_matches(self):
        self.assertIn('<div class="bars labelled pair">', self.page)

    def test_the_glyphs_the_markup_names_are_defined(self):
        """The renderers emit a class name and nothing else; if the stylesheet
        stops carrying the mask, both bars go back to saying nothing."""
        css = _stylesheet(self.page)
        for kind in ("lift", "escalator"):
            self.assertIn(f'class="kind kind-{kind}"', self.page)
            self.assertRegex(css, rf"\.kind-{kind} \{{[^}}]*--kind-icon:\s*url\(")
        self.assertRegex(css, r"\.kind \{[^}]*mask:\s*var\(--kind-icon\)")

    def test_a_glyph_in_the_legend_is_not_squashed_to_a_swatch(self):
        """statusui sizes legend swatches at 10px, which is fine for a square of
        colour and too small for a shape anyone has to recognise."""
        css = _stylesheet(self.page)
        self.assertRegex(statusui.base_css(), r"\.legend i \{[^}]*width: 10px")
        self.assertRegex(css, r"\.legend i\.kind \{[^}]*width: 15px")
        self.assertGreater(_specificity(".legend i.kind"), _specificity(".legend i"))

    def test_the_shared_reflow_still_places_bars_by_grid_area(self):
        """The premise. If this fails upstream has changed and the release below
        is dead weight rather than a fix."""
        self.assertRegex(statusui.base_css(), r"\.bar \{[^}]*grid-area: bar")

    def test_the_strips_inside_a_pair_are_released_from_it(self):
        css = _stylesheet(self.page)
        released = re.search(r"\.bars \.bar \{[^}]*grid-area:\s*auto", css)
        self.assertTrue(released, "the paired strips would stack on one grid line")
        # and it beats the shared rule wherever both match
        self.assertGreater(_specificity(".bars .bar"), _specificity(".bar"))


if __name__ == "__main__":
    unittest.main()
