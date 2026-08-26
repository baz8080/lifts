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
from collections import defaultdict
from datetime import timedelta
from pathlib import Path

import statusui

from lift_status.parse import DUBLIN

from . import model

BASE_URL = "https://baz8080.github.io/lifts"

TEMPLATES = Path(__file__).parent
SITE_HTML = TEMPLATES / "site.html"
STATION_HTML = TEMPLATES / "station.html"
SITE_CSS = TEMPLATES / "site.css"

# How far the data may lag the build before the page says so. The collector
# pushes at local midnight and noon with up to 30 minutes of jitter, so
# consecutive pushes can be 13.5 hours apart across a DST change, and the site
# rebuilds on every push to main as well as on its crons — a merge landing just
# before a push can build against data legitimately ~14 hours old. A collector
# that has actually died is first seen by the morning cron at 17+ hours. 16
# sits between the two; the numbers are in notes/site.md § The stale banner.
STALE_AFTER = timedelta(hours=16)

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


def build(outages, now, until):
    """Assemble every value the templates need, and nothing they do not.

    `now` fixes only what is still in the future; `until` is where the collected
    data stops, and every measured window ends there.
    """
    months = model.month_list(model.COLLECTION_START, now)
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
                # Five fields, and no more: the page reads m[0]..m[4], and
                # every byte here is in the initial load for every station.
                per_month[ym] = [
                    s["cells"], s["faults"], s["planned"], s["days_out"],
                    1 if s["ongoing"] else 0,
                ]
        stats[code] = per_month

    blank, national = {}, {}
    for ym in months:
        blank[ym] = model.station_month([], ym, now, until)["cells"]
        n = model.national_month(outages, ym, until)
        national[ym] = [
            n["stations"], n["outages"], n["faults"], n["planned"], n["station_days"], n["ongoing"],
        ]

    # What is listed at the horizon, for the banner: the state of the network
    # the last time anyone looked, which is not the same as the build clock.
    live = [o for o in outages if o.ongoing]
    current = {
        "stations": len({o.code for o in live}),
        "lifts": sum(1 for o in live if o.kind == "lift"),
        "escalators": sum(1 for o in live if o.kind == "escalator"),
    }

    data = {
        "generated": _stamp(now),
        # What the build knows, as distinct from when it ran. Without this the
        # page dates itself by the clock and a reader cannot tell a quiet week
        # from a collector that stopped.
        "observed": _stamp(until),
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
    }
    return data, by_station, months


def case_record(o):
    """One outage, as compact as it can be while staying readable in the file.

    The two durations are computed here, from the offset-aware instants, and
    shipped: `_short` renders Dublin wall-clock without an offset, so anything
    subtracting those strings loses the hour at the October clock change.
    """
    lead = None
    if o.start.astimezone(DUBLIN).date() < o.first_seen.astimezone(DUBLIN).date():
        lead = (o.first_seen - o.start).days
    return [
        o.id,
        o.kind,
        1 if o.planned else 0,
        _short(o.first_seen),
        _short(o.end),
        1 if o.ongoing else 0,
        _short(o.start),
        _short(o.listed_end),
        o.head,
        o.text or "",
        [[_short(when), head, text or ""] for when, head, text in o.updates],
        round((o.end - o.first_seen).total_seconds() / 3600.0, 4),
        lead,
    ]


def shard(outages, months, until):
    """Every outage at one station, grouped by month.

    An outage is listed under every month it overlaps, which is exactly the set
    of months `station_month` counts it in - so a reader can count the rows
    under a month and match the headline.
    """
    windows = [(ym,) + model.observed_window(ym, until) for ym in months]
    by_month = defaultdict(list)
    for o in sorted(outages, key=lambda o: (o.first_seen, o.id), reverse=True):
        record = None
        for ym, lo, hi in windows:
            if model.listed_in(o, lo, hi):
                record = case_record(o) if record is None else record
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
    bits.append("still listed at the last poll" if ongoing else f"no longer listed {_when(end)}")
    if start:
        claim = f"Irish Rail's notice dates it from {_when(start)}"
        if lead_days:
            claim += f" — {_days(lead_days)} before it was listed"
        bits.append(claim)
    if listed_end:
        bits.append(f"listed end {_when(listed_end)}")
    return bits


def _case_html(k):
    """The same markup site.html's caseHtml() builds, for the static page."""
    (kind, planned, first_seen, end, ongoing, start, listed_end,
     head, text, updates, hours, lead_days) = k[1:]
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


DAY_LABELS = {
    "0": "nothing listed",
    "1": "lift out of service",
    "2": "escalator out of service",
    "5": "planned works",
    "8": "no data collected for this day",
    "9": "still to come",
}


def _day_cells(cells, ym, partial):
    # nothing to qualify on a day with no data or no colour yet
    return statusui.day_cells(cells, ym, partial, DAY_LABELS, qualify=lambda ch: ch not in "89")


def station_page(code, data, by_month):
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
        f"service-message feed, since {data['start']}."
    )
    body = [
        '<a class="back" href="../index.html">← All stations</a>',
        '<div class="chead">',
        f"<h1>{html.escape(name)}</h1></div>",
        f'<div class="sub">Irish Rail station code {html.escape(code)}<br>'
        f'Data to {html.escape(data["observed"])}'
        + (
            ' · <span class="stale">collection has stopped</span>'
            if data["stale"]
            else ""
        )
        + "</div>",
    ]
    for ym in months:
        m = stats.get(ym)
        cells = m[0] if m else data["blank"][ym]
        cases = by_month.get(ym, [])
        body.append(f'<div class="card"><h2>{month_label(ym)}</h2>')
        body.append(f'<div class="bar tall">{_day_cells(cells, ym, data["partial"])}</div>')
        body.append('<div class="daycap"></div>')
        if cases:
            body.append("".join(_case_html(k) for k in cases))
        else:
            body.append(
                f'<p class="empty">Nothing listed for {html.escape(name)} in {month_label(ym)}.</p>'
            )
        body.append("</div>")
    body.append('<div class="card"><h2>Every station</h2><p class="nav">')
    body.append(
        " ".join(
            f'<a href="{data["slugs"][c]}.html">{html.escape(n)}</a>'
            for c, n in data["stations"].items()
            if c != code
        )
    )
    body.append("</p></div>")

    return _page(
        STATION_HTML,
        {
            "TITLE": html.escape(title),
            "DESC": html.escape(desc),
            "CANONICAL": f"{BASE_URL}/s/{data['slugs'][code]}.html",
            "BODY": "".join(body),
        },
    )


def _page(template, markers):
    """A template with the shared UI and this site's stylesheet inlined, then its markers."""
    markers = dict(markers, **{"SITE-CSS": SITE_CSS.read_text(encoding="utf-8")})
    return statusui.assemble(template.read_text(encoding="utf-8"), markers)


def write(site_dir, outages, now, until):
    site_dir = Path(site_dir)
    (site_dir / "s").mkdir(parents=True, exist_ok=True)
    (site_dir / "h").mkdir(parents=True, exist_ok=True)

    data, by_station, months = build(outages, now, until)

    (site_dir / "index.html").write_text(
        _page(SITE_HTML, {"CANONICAL": f"{BASE_URL}/"}), encoding="utf-8"
    )
    (site_dir / "data.js").write_text(
        "window.LIFT_DATA = " + _dumps(data) + ";\n", encoding="utf-8"
    )

    for code in data["stations"]:
        by_month = shard(by_station.get(code, []), months, until)
        # Shards are keyed by station code, which is short and URL-safe; the
        # static pages take the name so their URLs read well.
        (site_dir / "h" / f"{code}.js").write_text(
            f"(window.LIFT_CASES=window.LIFT_CASES||{{}})[{_dumps(code)}] = "
            + _dumps(by_month)
            + ";\n",
            encoding="utf-8",
        )
        (site_dir / "s" / f"{data['slugs'][code]}.html").write_text(
            station_page(code, data, by_month), encoding="utf-8"
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
