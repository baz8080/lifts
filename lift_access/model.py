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

# A sentence naming a platform reached without a lift: "Level to platform 1",
# Cork's "Platforms 1, 2, 3 and 4 are level". The exclusions do the work: a
# lift in the sentence makes it a sequence, stepped wording makes it not
# step-free, and "from platform" is a between-platform link that says nothing
# about the street leg. `notes/station-access.md`.
STEP_FREE = re.compile(r"\b(?:level|ramps?)\b", re.IGNORECASE)
STEPPED = re.compile(r"\b(?:stair\w*|steps?|footbridge|subway|escalators?)\b", re.IGNORECASE)
FROM_PLATFORM = re.compile(r"\bfrom\s+platforms?\b", re.IGNORECASE)
OTHER_KIND = {"lift": ESCALATOR, "escalator": LIFT}
SAME_KIND = {"lift": LIFT, "escalator": ESCALATOR}

# Naming the other machine as the way round is not naming it as broken. "The
# escalator at platform 2 is out of service. Please use the lift" is ordinary
# operator wording and the clearest statement of what happened, so forfeiting it
# loses the notices that say so outright. A sentence carrying outage wording is
# never a redirection: "use the stairs as the lift is out of service" names both.
# Not after "No.", which is a platform label (Athlone's "platforms No. 2 and 3")
# and not the end of a sentence.
SENTENCE = re.compile(r"(?<=[.!;])(?<!\b[Nn]o\.)\s+|\n")
REDIRECTION = re.compile(
    r"\b(?:use|using|via|take|taking)\s+(?:the\s+|a\s+|our\s+)?(?:lifts?|escalators?)\b",
    re.IGNORECASE,
)
OUT_OF_ACTION = re.compile(
    r"\b(?:out of (?:order|service|action)|unavailable|non[- ]operational|broken|faulty|"
    r"suspended|not (?:working|available|in (?:service|operation)))\b",
    re.IGNORECASE,
)

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

# Which leg of the journey a notice is about, read from its own text. A platform
# number or the word wins over an entrance word, because `platformAccess` starts
# at the ticket office: "the lift from the concourse to platform 2" is that
# field's leg. "at the main concourse" (Connolly) is the only entrance form on
# record; the rest of the list is the vocabulary of ticketOfficeAccess itself.
PLATFORM_LEG = "platform"
ENTRANCE_LEG = "entrance"
PLATFORM_WORD = re.compile(r"\bplatforms?\b", re.IGNORECASE)
ENTRANCE = re.compile(
    r"\b(?:concourse|entrances?|booking hall|ticket (?:office|hall)|car park|street level)\b",
    re.IGNORECASE,
)
# Kilcoole's ticketOfficeAccess is the two words "Not level", and "No ramp" would
# read the same way. A "No" before a number is a platform label: Carrigaloe's
# "platform No 2", Dalkey's "platform No 1", Athlone's "platforms No. 2 and 3".
NEGATED = re.compile(r"\b(?:no|not)\b(?!\.?\s*\d)", re.IGNORECASE)

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
    # journey: `platform_access` starts at the ticket office, so a notice that
    # names the way in ("at the main concourse") is read against this one. It is
    # the field literally about reaching the ticket office, so "No ticket office"
    # says nothing about the door.
    ticket_office_access: str
    lift_platforms: frozenset  # platforms the prose puts a lift at; may be {ALL_PLATFORMS}
    claims_lift: bool
    denies_lift: bool  # Dromod is the only station that says so outright


class Verdict(NamedTuple):
    state: str  # 'lost' | 'alternative' | 'escalator' | 'unknown'
    platforms: tuple
    detail: str
    leg: str | None = None  # PLATFORM_LEG | ENTRANCE_LEG | None when the notice says neither


def plain(fragment):
    """Rich-text HTML as plain text, with the block tags kept as separators.

    `[^>]*` and not `\\s*/?`: a `<br class="x">` from a CMS paste would miss the
    pattern, be stripped as an ordinary tag, and join two access lines into one.
    A merged segment naming a lift and two platforms records a lift at both, so
    "Ramp to platform 1" plus "Lift to platform 2" would publish "Platform 1 is
    reached by lift" - the false specific that specific-beats-general exists to
    prevent, arriving through a different door.
    """
    if not fragment:
        return ""
    text = re.sub(r"(?i)<(?:br|/p|/li|/h\d)\b[^>]*>", "\n", fragment)
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


def leg_named(text):
    """Which leg of the journey the notice puts the machine on, or None."""
    if not text:
        return None
    body = plain(text)
    if affected_platforms(body) or PLATFORM_WORD.search(body):
        return PLATFORM_LEG
    if ENTRANCE.search(body):
        return ENTRANCE_LEG
    return None


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


def _sentences(prose):
    """The prose one sentence at a time, boilerplate gone, in a quotable form.

    One splitter for every picker below, so the lift line, the level line and
    the reviewed quote cannot disagree about where a sentence ends.
    """
    return [
        sentence.strip().rstrip(".")
        for sentence in SENTENCE.split(strip_boilerplate(prose or ""))
        if sentence.strip()
    ]


def _level_sentences(prose):
    """The sentences that name a level or ramped way and nothing stepped."""
    return tuple(
        sentence
        for sentence in _sentences(prose)
        if STEP_FREE.search(sentence)
        and not (
            LIFT.search(sentence)
            or STEPPED.search(sentence)
            or FROM_PLATFORM.search(sentence)
            or NEGATED.search(sentence)
        )
    )


def step_free_platforms(station):
    """Every (platform, sentence) the prose reaches without a lift, in prose order.

    Read from the stored prose rather than kept on Station, so the claim can only
    ever quote a sentence still on the page.
    """
    found = []
    seen = set()
    for sentence in _level_sentences(station.platform_access):
        for platform in platforms_named(sentence):
            if platform not in seen:
                seen.add(platform)
                found.append((platform, sentence))
    return tuple(found)


def entrance_step_free(station):
    """The sentence naming a level or ramped way in, or None.

    No platform number is asked for on this leg: "Level access from car park" is
    as direct a statement as "Level to platform 1", and the way in has no number.
    """
    sentences = _level_sentences(station.ticket_office_access)
    return sentences[0] if sentences else None


def lift_sentence(prose, platforms=None, general_ok=False):
    """The sentence that puts a lift where the notice put its machine, or None.

    With no platforms, the first sentence naming a lift: the way in has one
    place, and Grand Canal Dock's names platform 2 on its way to saying so.
    Otherwise the first lift sentence naming one of the platforms, and a lift
    sentence naming none only if the caller says the page speaks generally -
    specific beats general, as in `read_platform_access`, which is what keeps
    Pearse's "Via ramps, stairs, escalators, and lifts." out of the quote.
    """
    general = None
    for sentence in _sentences(prose):
        if not LIFT.search(sentence) or DENIES_LIFT.search(sentence):
            continue
        if platforms is None:
            return sentence
        named = platforms_named(sentence)
        if named and set(named) & set(platforms):
            return sentence
        if not named and general is None:
            general = sentence
    return general if general_ok else None


def entrance_lift_sentence(station):
    """The sentence putting a lift on the way in, from either field, or None.

    ticketOfficeAccess first. Then platformAccess, where Pearse keeps its
    "Lifts/stairs/Escalators from the Pearse Street entrance": a lift the page
    does name must not be reported as one it does not.
    """
    quoted = lift_sentence(station.ticket_office_access)
    if quoted:
        return quoted
    for sentence in _sentences(station.platform_access):
        if (
            LIFT.search(sentence)
            and not DENIES_LIFT.search(sentence)
            and leg_named(sentence) == ENTRANCE_LEG
        ):
            return sentence
    return None


def entrance_lift(station):
    """Does Irish Rail's page put a lift on the way into the station?"""
    return entrance_lift_sentence(station) is not None


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


def implicated(pattern, body):
    """Does any sentence name this machine as broken, rather than as the way round?"""
    for sentence in SENTENCE.split(body):
        if not pattern.search(sentence):
            continue
        if REDIRECTION.search(sentence) and not OUT_OF_ACTION.search(sentence):
            continue
        return True
    return False


def _unknown(platforms, reason):
    return Verdict("unknown", tuple(platforms), reason)


def _still_note(station, serves, platforms):
    """The platforms that never needed the lift, when a lost verdict can say so.

    Lift-served platforms belong to the reviewed list. A platform the notice
    also names is two hand-written sources disagreeing, and so is a general lift
    claim beside a level line (Bray); stay quiet rather than pick a side.
    """
    if ALL_PLATFORMS in serves:
        return ""
    still = [
        (p, s) for p, s in step_free_platforms(station)
        if p not in serves and p not in platforms
    ]
    if not still:
        return ""
    labels = [p for p, _ in still]
    named = _join(labels)
    subject = (
        f"Platform {named} needed no lift, so it"
        if len(labels) == 1
        else f"Platforms {named} needed no lift, so they"
    )
    return f" {subject} kept step-free access: {_quoted(s for _, s in still)}."


def _quoted(sentences):
    """'"a" and "b"', each sentence once however many platforms it covers."""
    unique = []
    for sentence in sentences:
        if sentence not in unique:
            unique.append(sentence)
    return " and ".join(f'"{sentence}"' for sentence in unique)


def _join(labels):
    """"1", "1 and 2", "1, 2 and 3"."""
    return labels[0] if len(labels) == 1 else ", ".join(labels[:-1]) + " and " + labels[-1]


def _platform_phrase(platforms):
    if not platforms:
        return "the platforms"
    return f"platform{'s' if len(platforms) > 1 else ''} {_join(list(platforms))}"


def _escalator_verdict(station, named, leg, lift_listed_too):
    """The deduction, then what the page puts on the leg the notice named.

    The deduction is all that is *known*: an escalator has steps, so it was never
    a step-free route, so losing it cannot lose one. Who did lose something is
    the people an escalator serves, and whether they had another way up is a
    claim about the station that needs the station's own prose - on the same
    leg, because a lift to the platforms says nothing about the way in. Every
    sentence below quotes what the page names or says it names nothing; none
    says a lift was working, which the page cannot know and the site only ever
    knows in the negative (`lift_listed_too`).
    """
    parts = [
        "An escalator is moving stairs, so it was not a step-free route to begin with "
        "and its being out did not remove one. Anyone who finds a flight of stairs "
        "hard, or has a buggy, a suitcase or a stick, did lose a way up."
    ]
    if station is not None:
        # The flag is station-wide, so it says a lift notice was up and no more:
        # which lift is not established, and "that lift was out" would be.
        overlapped = ", though a lift notice at this station overlapped this one."
        if leg == PLATFORM_LEG:
            where = _platform_phrase(named)
            serves = station.lift_platforms
            lift = lift_sentence(
                station.platform_access,
                named or tuple(sorted(serves - {ALL_PLATFORMS})),
                general_ok=ALL_PLATFORMS in serves,
            )
            # A level platform has no level change for an escalator to make, so
            # a level line at the notice's platform is the two sources
            # disagreeing, and the rule for that is to say so, not pick a side.
            level = [
                (p, sentence)
                for p, sentence in step_free_platforms(station)
                if p in named and p not in serves
            ]
            level_platforms = {p for p, _ in level}
            # Every named platform gets one of three sentences: the lift the page
            # puts there, the level line it disagrees with, or that it has
            # neither. `covered` is what the first two accounted for.
            covered = set(level_platforms)
            if lift:
                # Phrased from the platforms the quoted sentence names, not the
                # notice's: Athy's "Lift to platform 2" beside a notice naming 1
                # and 2 must not put a lift on the way to the level platform. A
                # general claim (Bray's "Use the lift or stairs") is not put on
                # the way to a platform the same page calls level either.
                served = platforms_named(lift)
                if served:
                    at = tuple(p for p in named if p in served) or served
                else:
                    at = tuple(p for p in named if p not in level_platforms)
                if at or not named:
                    covered.update(at)
                    parts.append(
                        f"Irish Rail's page puts a lift on the way to {_platform_phrase(at)} "
                        "as well" + (overlapped if lift_listed_too else f': "{lift}".')
                    )
            if level:
                at = _platform_phrase(tuple(p for p, _ in level))
                it = "it" if len(level) == 1 else "them"
                parts.append(
                    f"Irish Rail's page calls {at} level: {_quoted(s for _, s in level)}, "
                    f"so the notice and the page disagree about {it}."
                )
            silent = tuple(p for p in named if p not in covered)
            if silent or (not named and len(parts) == 1):
                where = _platform_phrase(silent)
                if station.claims_lift:
                    parts.append(
                        f"Irish Rail's page names no lift or level way to {where}, so "
                        "nothing on it says there was another way up."
                    )
                else:
                    parts.append(
                        f"Irish Rail's page names no lift at {station.name}"
                        + (f" and no level way to {where}" if named else "")
                        + ", so nothing on it says there was another way up."
                    )
        elif leg == ENTRANCE_LEG:
            lift = entrance_lift_sentence(station)
            level = entrance_step_free(station)
            if lift:
                parts.append(
                    "Irish Rail's page puts a lift on the way into the station as well"
                    + (overlapped if lift_listed_too else f': "{lift}".')
                )
            if level:
                parts.append(f'Irish Rail\'s page names a level way into the station: "{level}".')
            if not lift and not level:
                parts.append(
                    "Irish Rail's page names no lift or level way into the station, so "
                    "nothing on it says there was another way up."
                )
        else:
            parts.append(
                "The notice does not say where the escalator is, so which way it served "
                "cannot be read against the page."
            )
        # Both fields: Connolly's escalator is named only in ticketOfficeAccess,
        # and Connolly is one of the three stations that has escalator notices.
        if not ESCALATOR.search(
            f"{station.platform_access or ''}\n{station.ticket_office_access or ''}"
        ):
            parts.append(f"Irish Rail's page for {station.name} does not mention an escalator.")
    return Verdict("escalator", named, " ".join(parts))


def _entrance_verdict(station, named):
    """A lift notice that puts the lift on the way in, read against that leg.

    Five pages put a lift there (Connolly, Clondalkin, Docklands, Grand Canal
    Dock in ticketOfficeAccess; Pearse in platformAccess). Clondalkin's "Level
    or via lift" is read as a loss like Hazelhatch's "lifts and ramps": the
    module does not parse connectives, and the quote lets a reader see the
    page's own words.

    Pearse's way-in field says "Level, through main entrance to the booking
    hall" and its platformAccess "Lifts/stairs/Escalators from the Pearse Street
    entrance". Reading only the first reported a lift the page names as one it
    does not; reading the notice on the platform leg instead published the ramp
    platform as kept, from a booking hall the notice's lift may be the way to.

    Returns None, for the caller to read the notice on the platform leg, only
    where the page's one lift sentence with an entrance word also names a
    platform ("Lift from the concourse to platform 2"): the page itself puts
    that lift on the platform leg, and the platform reading is the right one.
    """
    entry = station.ticket_office_access or ""
    quoted = entrance_lift_sentence(station)
    if not quoted and any(
        LIFT.search(s) and ENTRANCE.search(s) and not DENIES_LIFT.search(s)
        for s in _sentences(station.platform_access)
    ):
        return None
    if quoted:
        detail = (
            "The notice puts the lift on the way into the station, and Irish Rail's "
            f'page puts a lift there too: "{quoted}", so step-free access into the '
            "station was gone while this was listed."
        )
        level = entrance_step_free(station)
        if level:
            detail += f' Irish Rail\'s page also names a way in that needed no lift: "{level}".'
        return Verdict("lost", (), detail)
    return _unknown(
        named,
        "The notice puts the lift on the way into the station, and Irish Rail's page "
        f"for {station.name} "
        + ("names no lift on the way in" if entry.strip() else "says nothing about the way in")
        + ", so what it served is not recorded.",
    )


def verdict(station, kind, text, lift_listed_too=False):
    """What one notice means for step-free access at one station.

    The default is that a lift out removes step-free access to the platforms that
    lift serves, because on this network it nearly always does. Overstating access
    is the error worth engineering against: a reader who is told access is gone
    when it is not has made one wasted check, and a reader told the reverse is
    stranded on a platform.

    `lift_listed_too` is the one thing the site knows that the page does not: a
    lift notice at the same station was listed while this one was. Only the
    escalator sentence reads it, and only to withhold a lift the page names.
    """
    leg = leg_named(text)
    return _verdict(station, kind, text, leg, lift_listed_too)._replace(leg=leg)


def _verdict(station, kind, text, leg, lift_listed_too):
    named = affected_platforms(text)

    # `classify` reads the head, and the head is hand-written. A text naming only
    # the *other* machine means the head is probably wrong and the verdict turns
    # on which one it was. A text naming *both* is a combined outage, which is
    # the worst case for a reader and must not be forfeited: whatever else broke,
    # a lift notice whose text says "the lift and escalator at platform 2" still
    # has the lift out, so the platforms are still lost.
    body = plain(text) if text else ""
    if body and implicated(OTHER_KIND[kind], body):
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
        return _escalator_verdict(station, named, leg, lift_listed_too)

    if station is None:
        return _unknown(named, "This station is not in the station snapshot.")

    # Before `has_lift`, which reads the platform leg: a page can put a lift on
    # the way in and claim none to the platforms.
    if leg == ENTRANCE_LEG:
        result = _entrance_verdict(station, named)
        if result is not None:
            return result

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

    unlisted_note = (
        f" The notice also names platform {', '.join(unlisted)}, which the page "
        "does not list a lift at."
        if unlisted
        else ""
    )

    lost = [p for p in served if not _alternative(station, p)]
    if not lost:
        quoted = STEP_FREE_ALTERNATIVES[(station.code, served[0])]
        return Verdict(
            "alternative",
            tuple(served),
            f'Irish Rail\'s page names another step-free way here: "{quoted}".' + unlisted_note,
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
            "page. It needs reviewing again before this can be read either way."
            + unlisted_note,
        )

    listed = ", ".join(plain_loss)
    single = len(plain_loss) == 1
    subject = f"Platform {listed} is" if single else f"Platforms {listed} are"
    detail = (
        f"{subject} reached by lift, and Irish Rail's page names no other step-free "
        f"way to {'it' if single else 'them'}, so step-free access was gone while "
        "this was listed."
    )
    return Verdict(
        "lost", tuple(plain_loss), detail + _still_note(station, serves, platforms)
        + unlisted_note + stale_note
    )
