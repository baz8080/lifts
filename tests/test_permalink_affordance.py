"""The station view offers the page it has a permanent URL for.

This one already existed; what changed on 2026-08-26 is that it moved onto its
own line, so all three sites put the link in the same place, and it names the
station so a screen reader listing links out of context still reads.

Its wording stays address-flavoured while esb's and uisce's describe their
content, and that is deliberate: this page carries the same months and cases
the view does (see render.station_page), so naming it for its content would
promise a reader something they are already looking at.

Source-level rather than executed: this is a template string assembled at
runtime, and what needs guarding is that the link is still written at all.
"""

from __future__ import annotations

import unittest
from pathlib import Path

SITE_HTML = (Path(__file__).resolve().parent.parent / "lift_site" / "site.html").read_text()


class PermalinkAffordanceCase(unittest.TestCase):
    def test_the_station_view_links_to_the_station_page(self):
        self.assertIn("'<a href=\"s/' + D.slugs[code] + '.html\">", SITE_HTML)

    def test_the_link_has_its_own_line_under_the_heading(self):
        """It used to trail the descriptive sentence with a "·", which made it
        the least prominent of the three once esb and uisce gained theirs."""
        sub = SITE_HTML.index('\'<div class="sub">\'')
        link = SITE_HTML.index("'<a href=\"s/' + D.slugs[code] + '.html\">")
        self.assertLess(sub, link)
        self.assertIn("newest first<br>", SITE_HTML)

    def test_the_wording_stays_address_flavoured(self):
        """The page is the same content as the view, so it may not claim more."""
        self.assertIn("Permanent link to ", SITE_HTML)
        self.assertIn(" station</a>", SITE_HTML)
