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
    """Does this script declare `name` at the top level, in a form we can see?

    Column zero, one name per declaration - which is how every such line in
    these pages is written. What it does not see is a name that is the second
    or later declarator in a list: `var a = 1, esc = 2;` hides esc from it.

    That gap is left open on purpose. Four attempts to close it here each
    parsed JavaScript with a regex and each traded the narrow miss for a worse
    one: an array of shared helpers read as a redeclaration; a semicolon inside
    a string ended a statement early; a bracket in a caption made an ordinary
    object literal unreadable and broke the build. statusui holds its own
    bundle to one name per declaration by running it under a JavaScript engine.
    Nothing short of that belongs on this side, and nothing short of that is
    worth the false failures.
    """
    return bool(
        re.search(
            rf"^(?:async\s+)?(?:function|var|let|const|class)\s+{re.escape(name)}\b",
            script,
            re.M,
        )
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
