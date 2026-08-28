"""No page script may redeclare a global from statusui's shared bundle.

The bundle is inlined ahead of each page's own script, so a redeclaration
silently shadows the shared helper on that page alone.

The names come from `statusui.js_globals()`, never from reading `ui.js`: the
bundle is two files since the caption listener moved to `caption.js`, and a
test that reads one of them passes by seeing fewer names - which is a guard
failing open, silently, exactly when it stops covering something.
"""

import re
import unittest
from pathlib import Path

import statusui

HERE = Path(__file__).resolve().parent.parent

# A page takes the whole bundle or, if all it calls is the caption listener,
# that alone. Everything after whichever marker it carries is the page's own.
# From statusui, not spelled out here: a marker it renamed would leave this
# looking for a string no page carries, and failing to find one to check.
MARKERS = (statusui.UI_JS, statusui.UI_JS_CAPTION)


def declares(script, name):
    """Does this script declare `name` at the top level?

    Asked per name rather than by listing what the script declares, because
    listing misses the second name in `var a = 1, b = 2;` - a form site.html
    already uses - and a guard that misses a name fails open.

    Column zero only, which is what top level means here: a declaration inside
    a function body is scoped to that function and shadows nothing.
    """
    n = re.escape(name)
    if re.search(rf"^(?:function|var|let|const)\s+{n}\b", script, re.M):
        return True
    # a later declarator in one statement: `var a = 1, name = 2;`
    return any(
        re.search(rf",\s*{n}\s*(?:=|[,;]|$)", statement)
        for statement in re.findall(r"^(?:var|let|const)\b[^;]*", script, re.M)
    )


class TestUiGlobals(unittest.TestCase):
    def test_site_script_redeclares_no_shared_global(self):
        shared = statusui.js_globals()
        self.assertIn("bindDayCaption", shared, "the bundle's second file is missing")
        for page in ("site.html", "station.html"):
            text = (HERE / "lift_site" / page).read_text()
            marker = next((m for m in MARKERS if m in text), None)
            self.assertIsNotNone(marker, f"{page} inlines no shared script")
            own = text.split(marker, 1)[1]
            clashes = sorted(name for name in shared if declares(own, name))
            self.assertFalse(clashes, f"{page} redeclares {clashes}")
