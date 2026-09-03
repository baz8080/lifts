"""Emit the static site.

Same shape as the sibling esb site: `data.js` carries only what the front page
needs - one row per station per month, with the day bar packed into a string -
while the individual outages live in a per-station shard that is never fetched
until a reader opens that station. The corpus is tiny today, but the site is
meant to run for years, and the only way to keep the first download flat is to
never put a per-outage record in `data.js`.
"""

from __future__ import annotations

import html
import urllib.parse
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import statusui

from lift_access import model as access_model
from lift_status.parse import DUBLIN

from . import model

BASE_URL = "https://baz8080.github.io/lifts"
ISSUES_URL = "https://github.com/baz8080/lifts/issues/new"

# Said wherever a derived access claim appears. The derivation is careful and it
# is still an inference off a page somebody typed: this project has already found
# a typo in it, a self-contradiction, and a station whose page omits an escalator
# that exists. People who use these stations know things no source here records.
ACCESS_CAVEAT = (
    "Worked out from Irish Rail's own station page, which is written by hand and "
    "has been wrong before. It is a careful reading, not a survey, and it does not "
    "know about anything the page leaves out."
)
CORRECTION_PROMPT = "Know this station? Tell us what this gets wrong."

TEMPLATES = Path(__file__).parent
SITE_HTML = TEMPLATES / "site.html"
STATION_HTML = TEMPLATES / "station.html"
SITE_CSS = TEMPLATES / "site.css"

# How far the data may lag the build before the page says so. Pushes land every
# six hours, so with the timer's jitter and one poll interval the newest data can
# legitimately be ~7h old; a single missed push shows 13h+.
STALE_AFTER = timedelta(hours=10)

# What a reader downloads before touching anything. Named once: the build
# prints it, the build warns past it, and the render tests assert it.
BUDGET_BYTES = 500 * 1024

KIND_LABEL = {"lift": "Lift", "escalator": "Escalator"}

slug = statusui.slug
month_label = statusui.month_label
_dumps = statusui.dumps
_stamp = statusui.stamp
_days = statusui.days


def _short(dt):
    """An instant as the page shows it: Dublin wall-clock, to the minute.

    Rendered, never computed on, so minutes are enough - and local rather than
    UTC because the start Irish Rail writes on a notice is a Dublin time
    ("since 5 May, 00:00"), and quoting it back an hour earlier on the wrong
    date would misreport their claim. The build and horizon stamps stay UTC
    and say so.
    """
    return dt.astimezone(DUBLIN).strftime("%Y-%m-%dT%H:%M") if dt else None


def station_slugs(stations):
    """{code: slug}, made unique should two stations ever share a name."""
    slugs, taken = {}, set()
    for code, name in stations.items():
        s = slug(name) or code.lower()
        if s in taken:
            s = f"{s}-{code.lower()}"
        taken.add(s)
        slugs[code] = s
    return slugs


def build(outages, now, until, facts=None):
    """Assemble every value the templates need, and nothing they do not.

    `now` fixes only what is still in the future; `until` is where the collected
    data stops, and every measured window ends there.
    """
    # To the later of the two clocks: the horizon comes from the collector and
    # `now` from the builder, and a horizon in a month this list lacks would
    # drop that month's outages from the shards, the stats and the headline.
    months = model.month_list(model.COLLECTION_START, max(now, until))
    stations = model.station_index(outages)
    slugs = station_slugs(stations)

    by_station = defaultdict(list)
    for o in outages:
        by_station[o.code].append(o)

    # A station-month is stored only when something was listed. A quiet month
    # looks the same for every station, so its bar is stored once, under
    # `blank`, and the page falls back to it - the payload then grows with
    # outages rather than with stations × months.
    stats = {}
    for code, rows in by_station.items():
        per_month = {}
        for ym in months:
            s = model.station_month(rows, ym, now, until)
            if s["faults"] or s["planned"]:
                # Five fields, and no more, plus the escalator bar in the
                # months that had one: the page reads m[0]..m[5], and every
                # byte here is in the initial load for every station.
                per_month[ym] = [
                    s["cells"], s["faults"], s["planned"],
                    1 if s["ongoing"] else 0, s["avail"],
                ]
                if s["esc_cells"]:
                    per_month[ym].append(s["esc_cells"])
        stats[code] = per_month

    blank, national = {}, {}
    for ym in months:
        blank[ym] = model.station_month([], ym, now, until)["cells"]
        n = model.national_month(outages, ym, now, until)
        national[ym] = [
            n["stations"], n["outages"], n["faults"], n["planned"], n["avail"], n["ongoing"],
        ]

    # What is listed at the horizon, for the banner: the state of the network
    # the last time anyone looked, which is not the same as the build clock.
    live = [o for o in outages if o.ongoing]
    current = {
        "stations": len({o.code for o in live}),
        "lifts": sum(1 for o in live if o.kind == "lift"),
        "escalators": sum(1 for o in live if o.kind == "escalator"),
    }

    # Hand-reviewed in lift_access, never inferred from the prose.
    step_free = sorted(c for c in stations if _step_free_note(c, facts))

    # The feed names a station only when something is wrong with it, so a count
    # of them reads as the whole network without this.
    network = None
    if facts:
        tally = facts.tally()
        network = {
            "stations": len(facts.stations),
            "with_lift": tally["yes"],
            "no_lift": tally["no"],
        }

    data = {
        "generated": _stamp(now),
        "network": network,
        "stepfree": step_free,
        # Which stations the snapshot actually has prose for. The app renders
        # verdicts without the card that carries their source, and a single
        # global caveat printed "worked out from Irish Rail's page" above "this
        # station is not in the station snapshot".
        "access": sorted(c for c in stations if facts and facts.station(c)),
        # The app shows verdicts without the card that carries their source, so
        # the caveat travels with the payload rather than living only on the
        # static pages.
        "access_caveat": ACCESS_CAVEAT if facts else None,
        "correction_prompt": CORRECTION_PROMPT,
        "issues_url": ISSUES_URL,
        "base_url": BASE_URL,
        # What the build knows, as distinct from when it ran. Without this the
        # page dates itself by the clock and a reader cannot tell a quiet week
        # from a collector that stopped.
        "observed": _stamp(until),
        "observed_iso": f"{until:%Y-%m-%dT%H:%M:00Z}",
        "observed_month": f"{until.astimezone(DUBLIN):%Y-%m}",
        "stale_hours": round(STALE_AFTER.total_seconds() / 3600),
        "stale": now - until > STALE_AFTER,
        "partial": model.partial_days(until),
        "start": model.COLLECTION_START.strftime("%-d %B %Y"),
        # The same instant in the form the case records use, so the page can
        # say "already listed when collection began" with a string compare.
        "start_iso": _short(model.COLLECTION_START),
        "months": months,
        "stations": stations,
        "slugs": slugs,
        "stats": stats,
        "blank": blank,
        "national": national,
        "current": current,
        "legend": LEGEND_HTML,
        "grades": GRADE_SPANS,
        # The band table travels with the payload so the app derives a letter
        # the same way the static pages do, from the one table in the model.
        "bands": [list(b) for b in model.GRADE_BANDS],
    }
    return data, by_station, months


def case_record(o, facts=None, lift_listed_too=False):
    """One outage, as compact as it can be while staying readable in the file.

    The two durations are computed here, from the offset-aware instants, and
    shipped: `_short` renders Dublin wall-clock without an offset, so anything
    subtracting those strings loses the hour at the October clock change.

    The access verdict is shipped as a finished sentence rather than as parts.
    Everything else in this record is re-rendered by site.html's caseHtml(), so
    the wording lives twice; this one must not, because getting it wrong tells a
    reader access remains where it is gone. One function in lift_access writes
    it and both pages print it.
    """
    lead = None
    if o.start.astimezone(DUBLIN).date() < o.first_seen.astimezone(DUBLIN).date():
        lead = (o.first_seen - o.start).days
    # Irish Rail's end date is a placeholder near the end of the year on nearly
    # every notice, and the notice coming down is the completion signal. It is
    # worth showing while the works are still listed and misleading afterwards.
    listed_end = _short(o.listed_end) if o.ongoing else None
    return [
        o.id,
        o.kind,
        1 if o.planned else 0,
        _short(o.first_seen),
        _short(o.end),
        1 if o.ongoing else 0,
        _short(o.start),
        listed_end,
        o.head,
        o.text or "",
        [[_short(when), head, text or ""] for when, head, text in o.updates],
        round((o.end - o.first_seen).total_seconds() / 3600.0, 4),
        lead,
        _access(o, facts, lift_listed_too),
    ]


def _access(o, facts, lift_listed_too=False):
    """[state, sentence] for one outage, or None when no snapshot is loaded."""
    if not facts:
        return None
    result = facts.verdict(o.code, o.kind, o.text, lift_listed_too)
    return [result.state, result.detail]


def shard(outages, months, until, facts=None):
    """Every outage at one station, grouped by month.

    An outage is listed under every month it overlaps, which is exactly the set
    of months `station_month` counts it in - so a reader can count the rows
    under a month and match the headline.
    """
    windows = [(ym,) + model.observed_window(ym, until) for ym in months]
    # Computed here because this is the one place that holds all of a
    # station's outages: an escalator sentence must not quote a lift the row
    # above it shows was listed out at the same time. Half-open, so a lift that
    # came down at the poll the escalator went up (Pearse, 13 August) is not an
    # overlap. Station-wide rather than per platform: coarser only withholds.
    lifts = [x for x in outages if x.kind == "lift"]
    by_month = defaultdict(list)
    for o in sorted(outages, key=lambda o: (o.first_seen, o.id), reverse=True):
        overlapped = o.kind == "escalator" and any(
            x.first_seen < o.end and o.first_seen < x.end for x in lifts
        )
        record = None
        for ym, lo, hi in windows:
            if model.listed_in(o, lo, hi):
                record = case_record(o, facts, overlapped) if record is None else record
                by_month[ym].append(record)
    return by_month


def _when(ts):
    # starts can be a year old, so every instant carries its year
    return statusui.when(ts, year=True)


def _hours(h):
    return statusui.hours(h, _days)


COLLECTION_START_SHORT = _short(model.COLLECTION_START)


def summary_bits(first_seen, end, ongoing, start, listed_end, lead_days=None):
    """The words under an outage. Mirrored line for line in site.html's caseHtml().

    Two clocks, kept apart in the prose: when the notice was listed and taken
    down (observed here), and the start Irish Rail wrote on it (their claim).
    `lead_days` comes from case_record, computed on the offset-aware instants.
    """
    bits = [
        "listed when collection began"
        if first_seen <= COLLECTION_START_SHORT
        else f"first listed {_when(first_seen)}"
    ]
    bits.append(
        "still listed when we last checked" if ongoing else f"no longer listed {_when(end)}"
    )
    if start:
        claim = f"Irish Rail's notice dates it from {_when(start)}"
        if lead_days:
            claim += f" - {_days(lead_days)} before it was listed"
        bits.append(claim)
    if listed_end:
        bits.append(f"listed end {_when(listed_end)}")
    return bits


ACCESS_LABEL = {
    "lost": "No step-free access",
    "alternative": "Another step-free way",
    "escalator": "A way up lost, not step-free access",
    "unknown": "Effect on step-free access unknown",
}


def correction_url(name, code, page_slug):
    """A prefilled issue, which is the only feedback channel a static site has.

    Named and slugged from what the page is actually called, not from the
    snapshot: the site takes a station's display name from its newest notice and
    the snapshot has its own, and they differ. Re-deriving the slug here pointed
    Clondalkin's and Hazelhatch's reports at pages that do not exist, and gave
    the app and the static page two different titles for the same station.
    """
    body = (
        f"Station: {name} ({code})\n"
        f"{BASE_URL}/s/{page_slug}.html\n\n"
        "What this gets wrong, and how you know:\n"
    )
    query = urllib.parse.urlencode({"title": f"Station access: {name}", "body": body})
    return f"{ISSUES_URL}?{query}"


def _access_html(code, data, facts):
    """What Irish Rail's own page says this station has, quoted back.

    Quoted rather than summarised: every verdict on this page is derived from
    these sentences, and a reader who can see them can see when the derivation
    has read one wrong. That has already happened twice - see
    notes/station-access.md.

    Both legs of the journey, because they are different fields and a notice is
    read against the one it names. `ticketOfficeAccess` is how you reach the
    concourse from the street, which is where Connolly's escalator is and where
    `platformAccess` says nothing at all.
    """
    station = facts.station(code) if facts else None
    if station is None:
        return ""
    legs = [
        ("Into the station", station.ticket_office_access),
        ("To the platforms", station.platform_access),
    ]
    blocks = ""
    for label, prose in legs:
        if not prose:
            continue
        items = "".join(
            f"<li>{html.escape(line)}</li>" for line in prose.split("\n") if line
        )
        blocks += f"<h3>{label}</h3><ul>{items}</ul>"
    if not blocks:
        return ""
    note = _step_free_note(code, facts)
    earned = (
        f'<p class="sf"><b>{html.escape(STEP_FREE_CHIP)}.</b> '
        f'Reviewed against this line: "{html.escape(note)}".</p>'
        if note
        else ""
    )
    report = html.escape(
        correction_url(data["stations"][code], code, data["slugs"][code])
    )
    return (
        '<div class="card access"><h2>Getting to the platforms</h2>'
        f"{blocks}{earned}"
        f'<p class="src">{html.escape(ACCESS_CAVEAT)} '
        "A notice that names a platform is read against the second list, and one "
        "that names the concourse or entrance against the first. "
        f'<a href="{report}">{html.escape(CORRECTION_PROMPT)}</a></p></div>'
    )


def _verdict_html(access):
    """One outage's effect on step-free access, if a snapshot was loaded."""
    if not access:
        return ""
    state, detail = access
    return (
        f'<div class="acc acc-{html.escape(state)}">'
        f"<b>{html.escape(ACCESS_LABEL.get(state, state))}</b> "
        f"{html.escape(detail)}</div>"
    )


def _case_html(k):
    """The same markup site.html's caseHtml() builds, for the static page."""
    (kind, planned, first_seen, end, ongoing, start, listed_end,
     head, text, updates, hours, lead_days, access) = k[1:]
    span = ""
    if hours is not None:
        span = "listed " + _hours(hours) + (" so far" if ongoing else "")
    bits = summary_bits(first_seen, end, ongoing, start, listed_end, lead_days)
    return "".join(
        [
            f'<div class="case" id="m{k[0]}"><div class="top">',
            f'<span class="where">{html.escape(KIND_LABEL.get(kind, kind))}</span>',
            f'<span class="tag {"tag-p" if planned else "tag-f"}">'
            f'{"Planned works" if planned else "Out of service"}</span>',
            f'<span class="when">{span}</span></div>',
            f'<div class="sum">{" · ".join(html.escape(b) for b in bits)}</div>',
            f'<div class="txt">{html.escape(text)}</div>' if text else "",
            _verdict_html(access),
            _updates_html(updates),
            "</div>",
        ]
    )


def _updates_html(updates):
    if not updates:
        return ""
    items = "".join(
        f"<li><time>{_when(when)}</time>notice reissued: {html.escape(text or head)}</li>"
        for when, head, text in updates
    )
    return f'<ul class="tl">{items}</ul>'


def _day_labels(kind):
    """Cell captions for one kind's bar. The kind is the bar, not the colour."""
    return {
        "0": "nothing listed",
        "1": f"{KIND_LABEL[kind].lower()} out of service",
        "5": "planned works",
        "6": "planned works, listed over a week",
        "8": "no data collected for this day",
        "9": "still to come",
    }


def _day_cells(cells, ym, partial, kind="lift"):
    # nothing to qualify on a day with no data or no colour yet
    return statusui.day_cells(
        cells, ym, partial, _day_labels(kind), qualify=lambda ch: ch not in "89"
    )


STEP_FREE_CHIP = "Step-free route"

# Deliberately narrow. "Accessible station" would be a far bigger claim than the
# reviewed list makes, and the international access symbol would read as one.
STEP_FREE_TITLE = (
    "Irish Rail's page names a step-free way to a platform here that does not "
    "use the lift"
)


def _step_free_note(code, facts):
    """The sentence behind this station's chip, or None.

    Looks the station up rather than matching the code alone: an entry is only
    good while the prose it quotes is on the page, and a station absent from the
    snapshot has no prose to check. Chipping one anyway put an accessibility
    claim on a page whose own "Getting to the platforms" card was empty.
    """
    return access_model.step_free_note(facts.station(code)) if facts else None


def _step_free_chip(code, facts):
    """The same markup site.html's stepFreeChip() builds."""
    if not _step_free_note(code, facts):
        return ""
    return (
        f'<span class="sfchip" role="img" aria-label="{html.escape(STEP_FREE_TITLE)}" '
        f'title="{html.escape(STEP_FREE_TITLE)}">{STEP_FREE_CHIP}</span>'
    )


def _chip(letter, label):
    """The shared grade chip, with the name a screen reader reads for it.

    The letter alone is a letter: `role="img"` and the label are what make it a
    grade out loud. Mirrored in site.html's gradeChip().
    """
    return (
        f'<span class="gradechip g-{letter or "none"}" role="img" '
        f'aria-label="{html.escape(label)}" title="{html.escape(label)}">{letter or "-"}</span>'
    )


def _bar_label(cells, ym, kind):
    """What a bar says to a screen reader. Mirrored in site.html's barLabel().

    A month of empty `<i>`s conveys nothing on its own, and there is no reading
    of 31 day-cells that is worth listening to - so the bar is one image with
    one sentence, and the cases below it carry the detail.
    """
    watched = sum(1 for ch in cells if ch not in "89")
    listed = sum(1 for ch in cells if ch in "156")
    what = f"{KIND_LABEL[kind]}s in {month_label(ym)}"
    if not watched:
        return f"{what}: no data collected"
    days = f"{watched} day" + ("" if watched == 1 else "s")
    if not listed:
        return f"{what}: nothing listed on {days} watched"
    return f"{what}: listed on {listed} of {days} watched"


def _kind_cell(kind, tall):
    """What names the strip beside it: a glyph, and the word too where there is
    room for it.
    """
    icon = f'<i class="kind kind-{kind}" aria-hidden="true"'
    if not tall:
        return f'{icon} title="{KIND_LABEL[kind]}"></i>'
    return f"<span>{icon}></i>{KIND_LABEL[kind]}s</span>"


def _bars(cells, esc_cells, ym, partial, tall=False):
    """One bar, or a pair when the station had an escalator notice that month."""
    cls = "bar tall" if tall else "bar"
    lift = (
        f'<div class="{cls}" role="img" aria-label="{html.escape(_bar_label(cells, ym, "lift"))}">'
        f"{_day_cells(cells, ym, partial)}</div>"
    )
    wrap = "bars labelled" if tall else "bars"
    if not esc_cells:
        return f'<div class="{wrap}">{_kind_cell("lift", tall)}{lift}</div>'
    esc = (
        f'<div class="{cls}" role="img" '
        f'aria-label="{html.escape(_bar_label(esc_cells, ym, "escalator"))}">'
        f'{_day_cells(esc_cells, ym, partial, "escalator")}</div>'
    )
    # The pair splits one bar's height between them rather than doubling it.
    return (
        f'<div class="{wrap} pair">{_kind_cell("lift", tall)}{lift}'
        f'{_kind_cell("escalator", tall)}{esc}</div>'
    )


# What each day-cell colour means. The swatches take their colours from the
# same site.css rules that colour the cells, so the key cannot drift from the
# bars; the spans ship in data.js too, so the app's legend cannot drift from
# the static pages'.
LEGEND_ITEMS = (
    ("b0", "nothing listed"),
    ("b1", "out of service"),
    ("b5", "planned works"),
    ("b6", "planned works over a week"),
    ("b8", "no data"),
)

LEGEND_SPANS = "".join(
    f'<span><i class="{cls}"></i>{label}</span>' for cls, label in LEGEND_ITEMS
)

KIND_SPANS = "".join(
    f'<span><i class="kind kind-{kind}" aria-hidden="true"></i>{kind}</span>'
    for kind in ("lift", "escalator")
)


def _keys(name, spans):
    return f'<span class="keys" role="group" aria-label="{name}">{spans}</span>'


LEGEND_HTML = _keys("Which kind each bar carries", KIND_SPANS) + _keys(
    "What a day\'s colour means", LEGEND_SPANS
)

# The grade key, keyed by the letter rather than by a colour swatch. A reader
# identifies a grade by the letter in the chip - the colour behind it is
# reinforcement, and nothing else on the page is painted in it - so a row of
# plain swatches was a key to a code the page does not use, sitting directly
# under the day key, where every swatch does map to something in a bar.
# "A" is not "nothing listed": a planned-works notice inside its grace is on
# the bar and off the total, so the key says what the number means. The bands
# are days a reader can count - over a 22-day window B is one day listed, C two,
# D three to five, E up to half the window - which is why the key gives
# percentages and not adjectives.
GRADE_LABELS = (
    ("A", "100% available"),
    ("B", "95%+ available"),
    ("C", "90%+ available"),
    ("D", "75%+ available"),
    ("E", "50%+ available"),
    ("F", "under 50% available"),
)

GRADE_SPANS = "<span>Lift availability</span>" + "".join(
    f"<span>{_chip(letter, f'Grade {letter}')}{label}</span>"
    for letter, label in GRADE_LABELS
)


def _legend_html():
    return f'<div class="legend">{LEGEND_HTML}</div>'


def _station_links(codes, data):
    return " ".join(
        f'<a href="{data["slugs"][c]}.html">{html.escape(data["stations"][c])}</a>'
        for c in codes
    )


def _month_grade(m, blank_cells):
    """A month's availability and grade, from its row or from the quiet bar.

    A month with no row had nothing listed, which is 100% of the days that were
    watched - and no grade at all in a month that was not watched.
    """
    if m:
        return m[4], model.grade(m[4])
    avail = model.availability(sum(1 for ch in blank_cells if ch not in "89"), 0)
    return avail, model.grade(avail)


def month_sections(months, by_month, blank):
    """The page's months, with runs of quiet ones folded together.

    A station's page carries every month since collection began. A month it had
    a notice in is a card; a month it did not is a line, because twelve cards of
    identical bars and "nothing listed" is most of a year's page and most of its
    bytes. Watched and unwatched runs stay apart: a month nobody polled is not a
    month with nothing listed. Mirrored in site.html's monthSections().
    """
    out = []
    for ym in months:
        if by_month.get(ym):
            out.append(["card", ym, 0])
            continue
        watched = sum(1 for ch in blank[ym] if ch not in "89")
        if out and out[-1][0] == "quiet" and bool(out[-1][2]) == bool(watched):
            out[-1][1].append(ym)
            out[-1][2] += watched
        else:
            out.append(["quiet", [ym], watched])
    return out


def _quiet_row(yms, watched):
    """One line for a run of months with nothing listed."""
    span = month_label(yms[-1])
    if len(yms) > 1:
        span += f" to {month_label(yms[0])}"
    if not watched:
        return f'<div class="quiet">{span} · no data collected</div>'
    days = f"{watched} day" + ("" if watched == 1 else "s")
    return f'<div class="quiet">{span} · nothing listed, {days} watched</div>'


def _month_jumps(sections):
    """Anchors to the months that have a card, when there is more than one.

    The app's month strip is a row of buttons that swap the view; here the
    months are all on the page already, so the same strip is a set of links.
    """
    cards = [s[1] for s in sections if s[0] == "card"]
    if len(cards) < 2:
        return ""
    links = "".join(f'<a href="#ym-{ym}">{month_label(ym)}</a>' for ym in cards)
    return f'<div class="months jumps">{links}</div>'


def station_page(code, data, by_month, listed_now=(), facts=None):
    """A station's whole history on one page, newest month first.

    The page exists so a station has a real URL for a search engine and a
    reader arriving cold; it carries the same months and cases the app shows.
    """
    name = data["stations"][code]
    months = list(reversed(data["months"]))
    stats = data["stats"].get(code, {})
    title = f"Lift outages at {name} station"
    desc = (
        f"Lift (elevator) and escalator outages at {name} station, from Irish Rail's "
        f"service message feed, since {data['start']}."
    )
    # The month the data reaches, not the month the calendar reaches: if
    # collection stopped in August, August is the last month with a grade in it.
    # It can be a month the page does not carry, though - the months come from
    # the build clock and the horizon does not - and then the newest month the
    # page has is the only one it can honestly point at.
    latest = data["observed_month"]
    if latest not in data["blank"]:
        latest = data["months"][-1]
    letter = _month_grade(stats.get(latest), data["blank"][latest])[1]
    # The page carries every month, so a chip beside the name has to say which
    # month it is the grade for - in the sub line and in its own label.
    graded = f"graded on {month_label(latest)}"
    # Red says the record is not current. Why it is not is not something the page
    # can know: a stalled build looks exactly like a stalled collector.
    observed = html.escape(data["observed"])
    if data["stale"]:
        observed = f'<span class="stale">{observed}</span>'
    body = [
        '<a class="back" href="../index.html">← All stations</a>',
        '<div class="chead">',
        _chip(letter, f"Grade {letter} for {month_label(latest)}" if letter else "No grade yet"),
        f"<h1>{html.escape(name)}</h1>{_step_free_chip(code, facts)}</div>",
        f'<div class="sub">Irish Rail station code {html.escape(code)} · {graded}<br>'
        f"Data to {observed}</div>",
        _access_html(code, data, facts),
        _legend_html(),
    ]
    sections = month_sections(months, by_month, data["blank"])
    body.append(_month_jumps(sections))
    for kind, value, watched in sections:
        if kind == "quiet":
            body.append(_quiet_row(value, watched))
            continue
        ym = value
        m = stats.get(ym)
        avail, letter = _month_grade(m, data["blank"][ym])
        body.append(
            f'<div class="card" id="ym-{ym}">'
            f'<h2>{_chip(letter, f"Grade {letter}" if letter else "No grade")}'
            f"{month_label(ym)}"
            + (f'<span class="av">{avail}% of days available</span>' if avail is not None else "")
            + "</h2>"
        )
        esc = m[5] if m and len(m) > 5 else None
        body.append(_bars(m[0], esc, ym, data["partial"], tall=True))
        body.append('<div class="daycap"></div>')
        body.append("".join(_case_html(k) for k in by_month[ym]))
        body.append("</div>")
    # This card used to link every other station. That is a kilobyte of the
    # same links in the same order on every page a crawler fetches, and it grows
    # with the square of the station count. The index carries the full list
    # once; this says what else is out, which is the reason to leave this page.
    others = [c for c in listed_now if c != code]
    body.append('<div class="card"><h2>Out when we last checked</h2>')
    body.append(
        f'<p class="nav">{_station_links(others, data)}</p>'
        if others
        else '<p class="empty">Nothing else was out when we last checked.</p>'
    )
    body.append(
        '<p class="navmore"><a href="../index.html">Every station and its history</a></p>'
    )
    body.append("</div>")

    return _page(
        STATION_HTML,
        {
            "TITLE": html.escape(title),
            "DESC": html.escape(desc),
            "CANONICAL": f"{BASE_URL}/s/{data['slugs'][code]}.html",
            "GRADE-KEY": GRADE_SPANS,
            "BODY": "".join(body),
        },
    )


def _page(template, markers):
    """A template with the shared UI and this site's stylesheet inlined, then its markers."""
    markers = dict(markers, **{"SITE-CSS": SITE_CSS.read_text(encoding="utf-8")})
    return statusui.assemble(template.read_text(encoding="utf-8"), markers)


def write(site_dir, outages, now, until, facts=None):
    site_dir = Path(site_dir)
    (site_dir / "s").mkdir(parents=True, exist_ok=True)
    (site_dir / "h").mkdir(parents=True, exist_ok=True)

    data, by_station, months = build(outages, now, until, facts)

    # Every station page, linked from one page rather than from all of them.
    # The overview's own list is built by the app from data.js, so without this
    # a reader with no JavaScript - and a crawler that does not run it - has no
    # path to any station page at all.
    (site_dir / "index.html").write_text(
        _page(
            SITE_HTML,
            {
                "CANONICAL": f"{BASE_URL}/",
                "START": data["start"],
                "STATIONS": _station_links(data["stations"], data).replace('href="', 'href="s/'),
            },
        ),
        encoding="utf-8",
    )
    (site_dir / "data.js").write_text(
        "window.LIFT_DATA = " + _dumps(data) + ";\n", encoding="utf-8"
    )

    # The station pages link what was listed at the horizon, not at build time.
    listed_now = [c for c in data["stations"] if any(o.ongoing for o in by_station.get(c, []))]

    for code in data["stations"]:
        by_month = shard(by_station.get(code, []), months, until, facts)
        # Shards are keyed by station code, which is short and URL-safe; the
        # static pages take the name so their URLs read well.
        (site_dir / "h" / f"{code}.js").write_text(
            f"(window.LIFT_CASES=window.LIFT_CASES||{{}})[{_dumps(code)}] = "
            + _dumps(by_month)
            + ";\n",
            encoding="utf-8",
        )
        (site_dir / "s" / f"{data['slugs'][code]}.html").write_text(
            station_page(code, data, by_month, listed_now, facts), encoding="utf-8"
        )

    lastmod = now.strftime("%Y-%m-%d")
    paths = [""] + [f"s/{data['slugs'][c]}.html" for c in data["stations"]]
    (site_dir / "sitemap.xml").write_text(
        statusui.sitemap(BASE_URL, paths, lastmod), encoding="utf-8"
    )
    (site_dir / "robots.txt").write_text(statusui.robots(BASE_URL), encoding="utf-8")
    return data


def size_report(site_dir):
    """What a reader downloads before they touch anything; printed on every build."""
    return statusui.size_report(site_dir, BUDGET_BYTES, "s", "station pages")
