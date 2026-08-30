"""What a station has, and what a notice about it means for step-free access.

The one thing to understand before changing anything here: **`platformAccess`
prose is a description, not a route graph, and its "and" is a sequence rather
than a choice.** Hazelhatch's "All platforms can be accessed via lifts and ramps"
means you need both - the ramp gets you along, the lift does the level change -
and reading it as "either will do" publishes "access remains" at a station where
access is gone. Across the 61 stations whose prose mentions a lift, only two name
a genuine step-free alternative to one, and both are in STEP_FREE_ALTERNATIVES
below. So this module does not parse connectives at all: it works out which
platforms a lift serves, assumes an outage removes step-free access to them, and
carves out the two exceptions by hand. See `notes/station-access.md`.
"""

from __future__ import annotations

import html as html_module
import re
from typing import NamedTuple

# A segment that names a lift but no platform number applies to the whole
# station: "Lifts and footbridge to all platforms", "Lift to platforms".
ALL_PLATFORMS = "*"

# Pasted template text that appears verbatim at dozens of stations. It has to go
# before any keyword matching, because at Greystones, Killiney and Donabate it is
# the *only* mention of a lift, and leaving it in invents lifts nobody claimed.
BOILERPLATE = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(?:in order )?to access the lifts?,?\s*(?:you must (?:first )?call|"
        r"the customer is first required to call)[^.]*\.?",
        r"please see (?:our )?lift call operation page[^.]*\.?",
        r"blind passenger using (?:the )?lift call system[^.]*\.?",
        r"see our video of a blind passenger[^.]*",
        r"link:\s*youtube video",
    )
)

# "platform 2", "platforms No. 2 and 3", "platform 5A, 5B and 6", "Platform 1",
# "platforms  1 and 2" (Skerries really does have the double space).
PLATFORM_RUN = re.compile(
    r"\bplatforms?\b[\s.:]*(?:no\.?\s*)?"
    r"(\d+[A-Za-z]?(?:\s*(?:,|and|&|/|\bto\b)\s*(?:no\.?\s*)?\d+[A-Za-z]?)*)",
    re.IGNORECASE,
)
PLATFORM_SPLIT = re.compile(r"\s*(?:,|and|&|/|\bto\b)\s*", re.IGNORECASE)

LIFT = re.compile(r"\blifts?\b", re.IGNORECASE)
DENIES_LIFT = re.compile(r"\bno lift\b", re.IGNORECASE)

# Where the notice itself names the machine's platform. The head says only
# "Dublin Pearse - Lift out of order"; this has been in `text` all along.
AFFECTED = re.compile(
    r"\b(?:lifts?|escalators?)\b[^.]*?\bplatforms?\b[\s.:]*(?:no\.?\s*)?"
    r"(\d+[A-Za-z]?(?:\s*(?:,|and|&|/)\s*(?:no\.?\s*)?\d+[A-Za-z]?)*)",
    re.IGNORECASE,
)

# The complete list of places where Irish Rail's own prose names a step-free way
# round a lift, for the same platform. Two stations, checked by hand against the
# sentence quoted beside each. **Adding an entry is a human decision in a diff.**
# Nothing in this module may write to it, and no parser may infer one: "lift and
# ramp" is a sequence, and "lift or stairs" is not step-free.
STEP_FREE_ALTERNATIVES = {
    ("RAHNY", "1"): "Lift or ramp to platform 1 (City Centre and Southbound)",
    ("CORK", "5A"): "Ramp or lift to platform 5A, 5B and 6",
    ("CORK", "5B"): "Ramp or lift to platform 5A, 5B and 6",
    ("CORK", "6"): "Ramp or lift to platform 5A, 5B and 6",
}


class Station(NamedTuple):
    code: str
    name: str
    slug: str
    latitude: str | None
    longitude: str | None
    platform_access: str  # the prose, as published, for quoting back to a reader
    lift_platforms: frozenset  # platforms the prose puts a lift at; may be {ALL_PLATFORMS}
    claims_lift: bool
    denies_lift: bool  # Dromod is the only station that says so outright


class Verdict(NamedTuple):
    state: str  # 'lost' | 'alternative' | 'escalator' | 'unknown'
    platforms: tuple
    detail: str


def plain(fragment):
    """Rich-text HTML as plain text, with the block tags kept as separators."""
    if not fragment:
        return ""
    text = re.sub(r"(?i)<(?:br|/p|/li|/h\d)\s*/?>", "\n", fragment)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html_module.unescape(text).replace("\xa0", " ")
    return "\n".join(" ".join(line.split()) for line in text.split("\n"))


def strip_boilerplate(text):
    for pattern in BOILERPLATE:
        text = pattern.sub(" ", text)
    return "\n".join(" ".join(line.split()) for line in text.split("\n"))


def segments(fragment):
    """The prose as one line per block element, boilerplate removed."""
    return [line for line in strip_boilerplate(plain(fragment)).split("\n") if line]


def platforms_named(text):
    """Every platform label in a piece of text, in the order they appear."""
    found = []
    for run in PLATFORM_RUN.findall(text):
        for part in PLATFORM_SPLIT.split(run):
            label = re.sub(r"(?i)^no\.?\s*", "", part).strip().upper()
            if label and label not in found:
                found.append(label)
    return tuple(found)


def read_platform_access(fragment):
    """(lift_platforms, claims_lift, denies_lift) from one station's prose.

    A segment that names a lift and no platform is taken to mean every platform,
    which is what "Lifts and footbridge to all platforms" and "Lift to platforms"
    both say.
    """
    lift_platforms, claims, denies = set(), False, False
    for segment in segments(fragment):
        if DENIES_LIFT.search(segment):
            denies = True
            continue
        if not LIFT.search(segment):
            continue
        claims = True
        named = platforms_named(segment)
        lift_platforms.update(named or (ALL_PLATFORMS,))
    return frozenset(lift_platforms), claims, denies


def station_from_node(node, slug):
    """A Station from one resolved payload, or None if it carries no code."""
    if not isinstance(node, dict) or not node.get("stationCode"):
        return None
    fragment = (node.get("platformAccess") or {}).get("html") or ""
    lift_platforms, claims, denies = read_platform_access(fragment)
    return Station(
        code=str(node["stationCode"]).strip(),
        name=str(node.get("stationName") or "").strip(),
        slug=slug,
        latitude=node.get("latitude"),
        longitude=node.get("longitude"),
        platform_access=plain(fragment),
        lift_platforms=lift_platforms,
        claims_lift=claims,
        denies_lift=denies,
    )


def has_lift(station):
    """'yes' or 'no', for the station inventory.

    Irish Rail's own page is the only source. OpenStreetMap was carried here as
    a second opinion for a while and removed once it was measured: it changed no
    verdict, its one signal was redundant, and it could not answer the question
    that would have earned its keep. notes/station-access.md records what it can
    and cannot do, so nobody adds it back on the same hunch.
    """
    if station.denies_lift:
        return "no"
    return "yes" if station.claims_lift else "no"


def affected_platforms(text):
    """The platforms a notice names, or () when it names none."""
    if not text:
        return ()
    body = plain(text)
    found = []
    for run in AFFECTED.findall(body):
        for part in PLATFORM_SPLIT.split(run):
            label = re.sub(r"(?i)^no\.?\s*", "", part).strip().upper()
            if label and label not in found:
                found.append(label)
    return tuple(found)


def _unknown(platforms, reason):
    return Verdict("unknown", tuple(platforms), reason)


def verdict(station, kind, text):
    """What one notice means for step-free access at one station.

    The default is that a lift out removes step-free access to the platforms that
    lift serves, because on this network it nearly always does. Overstating access
    is the error worth engineering against: a reader who is told access is gone
    when it is not has made one wasted check, and a reader told the reverse is
    stranded on a platform.
    """
    if kind == "escalator":
        return Verdict(
            "escalator",
            affected_platforms(text),
            "An escalator is moving stairs, not a step-free route, so this did not "
            "remove step-free access.",
        )

    named = affected_platforms(text)
    if station is None:
        return _unknown(named, "This station is not in the station snapshot.")

    if has_lift(station) != "yes":
        return _unknown(
            named,
            f"Irish Rail's page for {station.name} does not mention a lift, so which "
            "platforms this one serves is not recorded.",
        )

    serves = station.lift_platforms
    platforms = named or (() if ALL_PLATFORMS in serves else tuple(sorted(serves)))

    if not platforms:
        return Verdict(
            "lost",
            (),
            "The notice names no platform, and Irish Rail's page puts a lift on the "
            "way to every platform here, so no platform had step-free access.",
        )

    if ALL_PLATFORMS in serves:
        served, unlisted = list(platforms), []
    else:
        served = [p for p in platforms if p in serves]
        unlisted = [p for p in platforms if p not in serves]

    # A notice naming platforms the page puts no lift at is a disagreement between
    # two hand-written sources, and this cannot tell which is stale. It only
    # forfeits the platforms it cannot vouch for: Athy's notice names 1 and 2
    # where the page has a lift at 2 and calls 1 level, and platform 2 is still
    # knowable.
    if not served:
        return _unknown(
            platforms,
            f"The notice names platform {', '.join(unlisted)}, which Irish Rail's page "
            f"for {station.name} does not list a lift at.",
        )

    lost = [p for p in served if (station.code, p) not in STEP_FREE_ALTERNATIVES]
    if not lost:
        quoted = STEP_FREE_ALTERNATIVES[(station.code, served[0])]
        return Verdict(
            "alternative",
            tuple(served),
            f'Irish Rail\'s page names another step-free way here: "{quoted}".',
        )

    listed = ", ".join(lost)
    subject = f"Platform {listed} is" if len(lost) == 1 else f"Platforms {listed} are"
    detail = (
        f"{subject} reached by lift, and Irish Rail's page names no other step-free "
        "way, so step-free access was gone while this was listed."
    )
    if unlisted:
        detail += (
            f" The notice also names platform {', '.join(unlisted)}, which the page "
            "does not list a lift at."
        )
    return Verdict("lost", tuple(lost), detail)
