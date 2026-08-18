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
import json
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

from lift_status.parse import DUBLIN

from . import model

BASE_URL = "https://baz8080.github.io/lifts"

TEMPLATES = Path(__file__).parent
SITE_HTML = TEMPLATES / "site.html"
STATION_HTML = TEMPLATES / "station.html"

CANONICAL = "<!--CANONICAL-->"
TITLE, DESC, BODY = "<!--TITLE-->", "<!--DESC-->", "<!--BODY-->"

# How far the data may lag the build before the page says so. The collector
# pushes daily and the site rebuilds daily, so a gap under this is the normal
# handover; past it, something has stopped and the reader should be told rather
# than left reading the day bars as a quiet week.
STALE_AFTER = timedelta(hours=24)

MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)

KIND_LABEL = {"lift": "Lift", "escalator": "Escalator"}


def slug(name):
    # Fadas folded to ASCII rather than dropped: "Dún Laoghaire" should read
    # as dun-laoghaire in the address bar, not d-n-laoghaire.
    folded = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return "".join(c if c.isalnum() else "-" for c in folded.lower()).strip("-")


def month_label(ym):
    return f"{MONTH_NAMES[int(ym[5:7]) - 1]} {ym[:4]}"


def _dumps(obj):
    # Default separators spend a byte on every comma and colon in the payload.
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def _stamp(dt):
    return dt.strftime("%Y-%m-%d %H:%M UTC")


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
                per_month[ym] = [
                    s["cells"], s["faults"], s["planned"], s["days_out"],
                    1 if s["ongoing"] else 0, s["lifts"], s["escalators"],
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
    """One outage, as compact as it can be while staying readable in the file."""
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
    if not ts:
        return ""
    dt = datetime.fromisoformat(ts)
    return f"{dt.day} {MONTH_NAMES[dt.month - 1][:3]} {dt.year}, {dt:%H:%M}"


def _hours(h):
    if h < 1:
        return f"{round(h * 60)} min"
    if h < 48:
        return f"{h:.1f} h" if h < 10 else f"{round(h)} h"
    return _days(round(h / 24))


def _days(n):
    if n < 2:
        return "1 day"
    if n < 60:
        return f"{n} days"
    return f"{n / 30.44:.1f} months"


COLLECTION_START_SHORT = _short(model.COLLECTION_START)


def summary_bits(first_seen, end, ongoing, start, listed_end):
    """The words under an outage. Mirrored line for line in site.html's caseHtml().

    Two clocks, kept apart in the prose: when the notice was listed and taken
    down (observed here), and the start Irish Rail wrote on it (their claim).
    """
    bits = [
        "listed when collection began"
        if first_seen <= COLLECTION_START_SHORT
        else f"first listed {_when(first_seen)}"
    ]
    bits.append("still listed at the last poll" if ongoing else f"no longer listed {_when(end)}")
    if start:
        claim = f"Irish Rail's notice dates it from {_when(start)}"
        if start < first_seen[:10]:
            days = (datetime.fromisoformat(first_seen) - datetime.fromisoformat(start)).days
            claim += f" — {_days(days)} before it was listed"
        bits.append(claim)
    if listed_end:
        bits.append(f"listed end {_when(listed_end)}")
    return bits


def _case_html(k):
    """The same markup site.html's caseHtml() builds, for the static page."""
    kind, planned, first_seen, end, ongoing, start, listed_end, head, text, updates = k[1:]
    span = ""
    if first_seen and end:
        hours = (
            datetime.fromisoformat(end) - datetime.fromisoformat(first_seen)
        ).total_seconds() / 3600.0
        span = "listed " + _hours(hours) + (" so far" if ongoing else "")
    bits = summary_bits(first_seen, end, ongoing, start, listed_end)
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


# Said on the two day cells built from part of a day. Plain words on purpose:
# it is read by someone wondering why their station looks quiet.
PARTIAL_NOTE = " — only part of this day was recorded"

DAY_LABELS = {
    "0": "nothing listed",
    "1": "lift out of service",
    "2": "escalator out of service",
    "5": "planned works",
    "8": "no data collected for this day",
    "9": "still to come",
}


def _day_cells(cells, ym, partial):
    out = []
    for i, ch in enumerate(cells):
        day = f"{ym}-{i + 1:02d}"
        cap = f"{day}: {DAY_LABELS[ch]}"
        if ch not in "89" and day in partial:
            cap += PARTIAL_NOTE
        out.append(f'<i class="b{ch}" title="{html.escape(cap)}"></i>')
    return "".join(out)


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
    latest = stats.get(months[0])
    out_now = bool(latest and latest[4])
    body = [
        '<a class="back" href="../index.html">← All stations</a>',
        f'<div class="chead"><span class="dot {"d-out" if out_now else "d-ok"}"></span>',
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
        body.append(f'<div class="bar">{_day_cells(cells, ym, data["partial"])}</div>')
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

    page = STATION_HTML.read_text(encoding="utf-8")
    return (
        page.replace(TITLE, html.escape(title))
        .replace(DESC, html.escape(desc))
        .replace(CANONICAL, f"{BASE_URL}/s/{data['slugs'][code]}.html")
        .replace(BODY, "".join(body))
    )


def _sitemap(paths, lastmod):
    urls = "".join(
        f"<url><loc>{BASE_URL}/{p}</loc><lastmod>{lastmod}</lastmod></url>" for p in paths
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>"
    )


def write(site_dir, outages, now, until):
    site_dir = Path(site_dir)
    (site_dir / "s").mkdir(parents=True, exist_ok=True)
    (site_dir / "h").mkdir(parents=True, exist_ok=True)

    data, by_station, months = build(outages, now, until)

    (site_dir / "index.html").write_text(
        SITE_HTML.read_text(encoding="utf-8").replace(CANONICAL, f"{BASE_URL}/"),
        encoding="utf-8",
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
    (site_dir / "sitemap.xml").write_text(_sitemap(paths, lastmod), encoding="utf-8")
    (site_dir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    return data


def size_report(site_dir):
    """What a reader downloads before they touch anything.

    Printed on every build: the payload is the constraint this site has to keep
    defending as the corpus grows, and a regression belongs in the build log.
    """
    site_dir = Path(site_dir)
    initial = {p: (site_dir / p).stat().st_size for p in ("index.html", "data.js")}
    shards = sorted((site_dir / "h").glob("*.js"), key=lambda p: -p.stat().st_size)
    pages = list((site_dir / "s").glob("*.html"))
    lines = [
        f"  {'index.html':<16}{initial['index.html'] / 1024:8.1f} KB",
        f"  {'data.js':<16}{initial['data.js'] / 1024:8.1f} KB",
        f"  {'initial load':<16}{sum(initial.values()) / 1024:8.1f} KB"
        f"   (budget 500.0 KB)",
        f"  {'station pages':<16}{sum(p.stat().st_size for p in pages) / 1024:8.1f} KB"
        f"   ({len(pages)} files)",
    ]
    if shards:
        lines.append(
            f"  {'shards':<16}{sum(p.stat().st_size for p in shards) / 1024:8.1f} KB"
            f"   ({len(shards)} files, largest {shards[0].name} at"
            f" {shards[0].stat().st_size / 1024:.1f} KB)"
        )
    return sum(initial.values()), "\n".join(lines)
