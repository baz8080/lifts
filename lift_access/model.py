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
        r"the customer is first required to call)[^.\n]*\.?",
        r"please see (?:our )?lift call operation page[^.\n]*\.?",
        r"blind passenger using (?:the )?lift call system[^.\n]*\.?",
        r"see our video of a blind passenger[^.\n]*",
        r"link:\s*youtube video",
    )
)

# "platform 2", "platforms No. 2 and 3", "platform 5A, 5B and 6", "Platform 1",
# "platforms  1 and 2" (Skerries really does have the double space).
# `to` is not among the separators: it would read "platforms 1 to 4" as 1 and 4
# and drop the two in the middle. The "to" in "Lift to platform 2" sits before
# the word platform, which is matched separately.
PLATFORM_RUN = re.compile(
    r"\bplatforms?\b[\s.:]*(?:no\.?\s*)?"
    r"(\d+[A-Za-z]?(?:\s*(?:,|and|&|/)\s*(?:no\.?\s*)?\d+[A-Za-z]?)*)",
    re.IGNORECASE,
)
PLATFORM_SPLIT = re.compile(r"\s*(?:,|and|&|/)\s*", re.IGNORECASE)

LIFT = re.compile(r"\blifts?\b", re.IGNORECASE)
ESCALATOR = re.compile(r"\bescalators?\b", re.IGNORECASE)
DENIES_LIFT = re.compile(r"\bno lift\b", re.IGNORECASE)
OTHER_KIND = {"lift": ESCALATOR, "escalator": LIFT}
SAME_KIND = {"lift": LIFT, "escalator": ESCALATOR}

# Where the notice itself names the machine's platform. The head says only
# "Dublin Pearse - Lift out of order"; this has been in `text` all along.
# `[^.\n]` and not `[^.]`: the class is one literal dot, so it would match a
# newline, and `plain()` turns the `<br>` the feed puts in `text` into one. That
# let "The lift is out of service<br>Trains depart from platform 3" read as a
# lift at platform 3.
AFFECTED = re.compile(
    r"\b(?:lifts?|escalators?)\b[^.\n]*?\bplatforms?\b[\s.:]*(?:no\.?\s*)?"
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
    # How you get from the street to the concourse. A separate leg of the
    # journey, and the derivation does not model it: `platform_access` starts at
    # the ticket office. Read here only so the page can quote it and so the
    # escalator check can see Connolly's, which is named nowhere else.
    ticket_office_access: str
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

    A segment that names a lift and no platform means every platform - "Lifts and
    footbridge to all platforms", "Lift to platforms" - but **only if no other
    segment names one specifically**. Pearse opens with a summary, "Via ramps,
    stairs, escalators, and lifts.", and then says "Ramp to platform 1" and "Lift
    or stairs to platform 2". Read as a per-platform claim the summary makes the
    lift serve platform 1 too, and the site tells a reader the ramp platform lost
    step-free access. Specific beats general, and a station that names none is
    the only one that gets ALL_PLATFORMS.
    """
    specific, general, claims, denies = set(), False, False, False
    for segment in segments(fragment):
        if DENIES_LIFT.search(segment):
            denies = True
            continue
        if not LIFT.search(segment):
            continue
        claims = True
        named = platforms_named(segment)
        if named:
            specific.update(named)
        else:
            general = True
    if specific:
        return frozenset(specific), claims, denies
    return frozenset({ALL_PLATFORMS} if general else ()), claims, denies


def station_from_node(node, slug):
    """A Station from one resolved payload, or None if it carries no code."""
    if not isinstance(node, dict) or not node.get("stationCode"):
        return None
    fragment = (node.get("platformAccess") or {}).get("html") or ""
    entry = (node.get("ticketOfficeAccess") or {}).get("html") or ""
    lift_platforms, claims, denies = read_platform_access(fragment)
    return Station(
        code=str(node["stationCode"]).strip(),
        name=str(node.get("stationName") or "").strip(),
        slug=slug,
        latitude=node.get("latitude"),
        longitude=node.get("longitude"),
        platform_access=plain(fragment),
        ticket_office_access=plain(entry),
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


def step_free_note(station):
    """The sentence behind a station's step-free chip, or None.

    Asks the same question `_alternative` asks, so the chip and the verdict
    cannot disagree: a reworded page withdraws both at once.
    """
    if station is None:
        return None
    for (code, platform), sentence in STEP_FREE_ALTERNATIVES.items():
        if code == station.code and _alternative(station, platform):
            return sentence
    return None


def _alternative(station, platform):
    """Is there a reviewed step-free way round the lift, and does the page still say so?

    The entry quotes a sentence, and the page it was quoted from is refetched
    every month precisely because Irish Rail rewords these. If the sentence has
    gone, the review no longer describes the station: the entry stops applying
    until somebody looks again. Saying "another step-free way remains" on the
    strength of a sentence that has been deleted is the exact error this module
    is built to avoid.
    """
    quoted = STEP_FREE_ALTERNATIVES.get((station.code, platform))
    return bool(quoted) and quoted in " ".join((station.platform_access or "").split())


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
    named = affected_platforms(text)

    # `classify` reads the head, and the head is hand-written. A text naming only
    # the *other* machine means the head is probably wrong and the verdict turns
    # on which one it was. A text naming *both* is a combined outage, which is
    # the worst case for a reader and must not be forfeited: whatever else broke,
    # a lift notice whose text says "the lift and escalator at platform 2" still
    # has the lift out, so the platforms are still lost.
    body = plain(text) if text else ""
    if body and OTHER_KIND[kind].search(body):
        this_kind_too = SAME_KIND[kind].search(body)
        # An escalator outage is the one verdict that is a deduction rather than
        # a reading, and it is only safe while nothing else is implicated: saying
        # an escalator was never step-free is no comfort if a lift went with it.
        if not this_kind_too or kind == "escalator":
            return _unknown(
                named,
                f"The notice is headed as a {kind} but its text names the other machine "
                + ("as well, so what was out is not established."
                   if this_kind_too
                   else "instead, so which one was out is not established."),
            )

    if kind == "escalator":
        # The deduction, and only the deduction: an escalator has steps, so it was
        # never a step-free route, so losing it cannot lose one. That says nothing
        # about whether the station still has step-free access by some other way,
        # which is a claim about the station and needs the station's own prose.
        detail = (
            "An escalator is moving stairs, so it was not a step-free route to begin "
            "with and its being out did not remove one."
        )
        # Both fields: Connolly's escalator is named only in ticketOfficeAccess,
        # and Connolly is one of the two stations that has escalator notices.
        named_here = station is not None and ESCALATOR.search(
            f"{station.platform_access or ''}\n{station.ticket_office_access or ''}"
        )
        if station is not None and not named_here:
            detail += (
                f" Irish Rail's page for {station.name} does not mention an escalator, "
                "so what this one served is not recorded."
            )
        return Verdict("escalator", named, detail)

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

    lost = [p for p in served if not _alternative(station, p)]
    if not lost:
        quoted = STEP_FREE_ALTERNATIVES[(station.code, served[0])]
        return Verdict(
            "alternative",
            tuple(served),
            f'Irish Rail\'s page names another step-free way here: "{quoted}".',
        )

    # A reviewed entry whose sentence has gone off the page forfeits *its* own
    # platform and no others. Cork has entries for 5A, 5B and 6: a reworded page
    # must not take platform 7 down with them when 7 has no entry, is lift-served
    # and is plainly lost. Same partition as `unlisted` above.
    stale = [p for p in lost if (station.code, p) in STEP_FREE_ALTERNATIVES]
    plain_loss = [p for p in lost if (station.code, p) not in STEP_FREE_ALTERNATIVES]
    stale_note = (
        f" A reviewed step-free alternative is on file for platform {', '.join(stale)}, "
        "but the sentence it quotes is no longer on Irish Rail's page, so that platform "
        "needs reviewing again."
        if stale
        else ""
    )
    if not plain_loss:
        return _unknown(
            tuple(stale),
            f"A reviewed step-free alternative is on file for platform {', '.join(stale)} "
            f"at {station.name}, but the sentence it quotes is no longer on Irish Rail's "
            "page. It needs reviewing again before this can be read either way.",
        )

    listed = ", ".join(plain_loss)
    subject = f"Platform {listed} is" if len(plain_loss) == 1 else f"Platforms {listed} are"
    detail = (
        f"{subject} reached by lift, and Irish Rail's page names no other step-free "
        "way, so step-free access was gone while this was listed."
    )
    if unlisted:
        detail += (
            f" The notice also names platform {', '.join(unlisted)}, which the page "
            "does not list a lift at."
        )
    return Verdict("lost", tuple(plain_loss), detail + stale_note)
