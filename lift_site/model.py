"""Turning the message database into per-station, per-month statistics.

The feed is a list of every service-message banner Irish Rail currently shows,
of which a handful are "<Station> - Lift out of order". This module picks those
out (and the escalator ones), files them under the station they name, and works
out for every day of every month whether a notice was listed.

That is the whole measurement. The feed carries no magnitude - a notice is
either listed or it is not - so a day cell says only that, and the grade counts
those days: the share of the days watched on which nothing was listed. The words
the site uses are "listed" and "no longer listed", never "fixed": a notice
vanishing means Irish Rail took it down, which is usually but not provably the
same thing.

Every interval measured here is the one the notice was *listed* for. The start
date Irish Rail writes on a notice is shown but never measured: it routinely
predates the listing by months, over days the feed was watched and the notice
was not there. See notes/site.md for the numbers behind that.
"""

from __future__ import annotations

import calendar
import json
import re
import sqlite3
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from typing import NamedTuple

from lift_status.parse import DUBLIN

# The first poll landed at 2026-08-08T21:30:55Z. The feed only ever shows the
# notices currently up, so nothing before this instant exists anywhere and days
# before it are rendered as "no data", never as "in service".
COLLECTION_START = datetime(2026, 8, 8, 21, 30, 55, tzinfo=UTC)

# What a step-free-access notice looks like in `head`, as observed live:
# "Rush and Lusk - Lift out of order", "Skerries - Lifts out of order",
# "Thurles - Lift out of service", "Connolly - Escalator out of order".
# Everything else in the feed - delays, cancellations, "Station currently
# closed" - is not this site's subject and is ignored.
KIND_PATTERNS = (
    ("lift", re.compile(r"\blifts?\b.*\bout of (order|service)\b", re.IGNORECASE)),
    ("escalator", re.compile(r"\bescalators?\b.*\bout of (order|service)\b", re.IGNORECASE)),
)

# "temporarily unavailable due to planned works" versus "currently out of
# service" - the one distinction the notice text draws that a reader cares about.
PLANNED_MARKER = "planned works"

# Day-cell codes. One character per day of the month, packed into a string.
# A bar carries one kind - a station gets a lift bar and, in a month it had an
# escalator notice, an escalator bar - so the code says what was listed and the
# bar it sits in says which kind. There is no escalator code any more.
DAY_CLEAR = 0  # nothing listed at this station
DAY_OUT = 1  # a notice that is not planned works
DAY_PLANNED = 5  # planned works only
DAY_NO_DATA = 8  # outside the window the collector actually covered
DAY_FUTURE = 9

# How long a planned-works notice may stand before its days count against
# availability. A week is a plausible maintenance window; the notices that sit
# for months are unavailability with a label on it, and Irish Rail's own end
# dates are placeholders, so the listing is the only measure of the works.
PLANNED_GRACE = timedelta(days=7)

# The scale is this site's own. There is no Irish or EU target to grade
# against: the PRM TSI (Regulation (EU) 1300/2014) sets lift and escalator
# design rules and a duty on the station manager to hold a written access
# policy, not a number, and Irish Rail's charter promises only "every effort".
# So the bands are calibrated in days a reader can count: over a 31-day month,
# B is one day listed, C two or three, D up to a week.
GRADE_BANDS = ((100, "A"), (95, "B"), (90, "C"), (75, "D"), (0, "F"))

# Notices are re-issued when Irish Rail edits the wording or corrects a start
# time; the collector sees that as the old notice closing and a new one opening
# in the same poll (the README's "identity drift"). Those are one outage to a
# reader. A notice that reappears a poll or more later is a separate row: the
# gap is real information, since it is exactly what the site is measuring.
# `merge_edits` folds only the same-poll case.


def parse_utc(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _local(dt):
    """An instant as Dublin wall-clock, which is the clock the site files by."""
    return dt.astimezone(DUBLIN)


def _month_start(dt):
    """The Dublin midnight that begins `dt`'s month."""
    return _local(dt).replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def month_bounds(ym):
    year, month = int(ym[:4]), int(ym[5:7])
    lo = datetime(year, month, 1, tzinfo=DUBLIN)
    hi = datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=DUBLIN)
    return lo, hi


def month_list(start, end):
    # From the month `start` falls in, by Dublin months. The time of day is
    # dropped deliberately: keeping COLLECTION_START's 21:30 would hide a month
    # from every build that ran earlier in the day than that on the 1st.
    # The month collection began in is always one of them, even for a build
    # clock earlier than the first poll: every caller indexes this list, and no
    # months at all is not a shorter answer, it is an IndexError.
    months, cur = [], _month_start(start)
    while cur <= end or not months:
        months.append(f"{cur.year:04d}-{cur.month:02d}")
        cur = _month_start(cur + timedelta(days=32))
    return months


def classify(head):
    """'lift', 'escalator', or None for a notice that is neither."""
    if not head:
        return None
    for kind, pattern in KIND_PATTERNS:
        if pattern.search(head):
            return kind
    return None


def is_planned(text):
    return bool(text) and PLANNED_MARKER in text.lower()


def station_of(row):
    """(code, display name) for a message row.

    Every lift/escalator notice observed so far names exactly one location
    code, and its `eventStops[0].sStop` carries the full station name ("Dublin
    Connolly" where the head says just "Connolly"). The code is the identity;
    the name is for display, and the head's prefix is the fallback when a
    notice arrives without stops.
    """
    codes = json.loads(row["location_codes"]) if row["location_codes"] else []
    code = codes[0] if codes else "?"
    name = None
    if row["event_stops"]:
        try:
            stops = json.loads(row["event_stops"])
        except (TypeError, ValueError):
            stops = None
        if isinstance(stops, list) and stops and isinstance(stops[0], dict):
            candidate = stops[0].get("sStop")
            if isinstance(candidate, str) and candidate.strip():
                name = candidate.strip()
    if not name:
        head = row["head"] or ""
        name = head.split(" - ", 1)[0].strip() or code
    return code, name


class Outage(NamedTuple):
    """One notice's life on the feed.

    Two clocks, and the site is careful which it uses. `first_seen` to `end` is
    the interval the notice was *listed*, as observed - that is what the day
    bars, the month filing and the durations measure. `start` is the date Irish
    Rail wrote on the notice, which routinely predates the listing by months
    (Ballybrophy: "since 5 May", listed 13-14 August); it is shown on the
    outage as Irish Rail's claim and measured nowhere, because the feed was
    watched on the days between and the notice was not there.
    """

    id: int  # the first message row it was built from
    code: str
    station: str
    kind: str  # 'lift' | 'escalator'
    planned: bool
    start: datetime  # Irish Rail's reported start; may predate collection
    first_seen: datetime  # the poll this site first saw the notice at
    end: datetime  # first poll it was absent from, or the horizon if still up
    ongoing: bool
    listed_end: datetime | None  # Irish Rail's `end`, shown but not trusted
    head: str
    text: str | None
    updates: tuple  # ((when, head, text), ...) for notices folded in by merge_edits
    # ((first_seen, end, planned), ...), one per notice folded in. A merged
    # outage takes its wording and works flag from the newest notice, but a day
    # is coloured by what was listed *that* day - so a planned-works notice
    # replaced by a fault does not repaint the planned days red.
    segments: tuple = ()


def observed_until(conn):
    """The last instant the collector is known to have read the feed.

    Taken from runs that reached the API and parsed it, not from the notices:
    a poll that listed no lift outages still observed that none were listed.
    Deliberately not `now` - the build clock keeps moving whether or not the
    Raspberry Pi is still polling, and a site that treats "no data" as "in
    service" publishes a clean bill of health for days nobody watched.

    Nothing falls back to the notices: a message row is only ever written
    between `begin_run_success` (which stamps outcome='ok') and `finalize_run`,
    in one transaction, so a message can never outlive the ok run that saw it.
    """
    row = conn.execute(
        "SELECT MAX(started_at_utc) AS t FROM runs WHERE outcome = 'ok'"
    ).fetchone()
    return parse_utc(row["t"])


def _outage_from_row(row, until):
    kind = classify(row["head"])
    if kind is None:
        return None
    code, station = station_of(row)
    first_seen = parse_utc(row["first_seen_at_utc"])
    # An unparseable start falls back to when the notice was first listed.
    start = parse_utc(row["start_utc"]) or first_seen
    ongoing = row["status"] == "open"
    end = until if ongoing else parse_utc(row["closed_at_utc"])
    if end is None:
        # A closed row always has closed_at_utc; guard anyway rather than
        # publish an outage with no end.
        end = parse_utc(row["last_seen_at_utc"])
    planned = is_planned(row["text_raw"])
    return Outage(
        id=row["id"],
        code=code,
        station=station,
        kind=kind,
        planned=planned,
        start=start,
        first_seen=first_seen,
        end=end,
        ongoing=ongoing,
        listed_end=parse_utc(row["end_utc"]),
        head=row["head"],
        text=row["text_raw"],
        updates=(),
        segments=((first_seen, end, planned),),
    )


def merge_edits(outages):
    """Fold a notice that replaced another in the same poll into one outage.

    Same station, same kind, and the newer notice first seen at the very poll
    the older one went missing - the collector's `closed_at_utc` is that poll's
    timestamp, so equality is exact rather than a tolerance. Two notices open at
    the same station at once (one per lift) are left as two rows: the older is
    still listed when the newer appears, so the equality never holds.

    The merged outage is listed from the first notice's appearance to the last
    one's removal, keeps the earliest reported start, takes its wording,
    kind-of-works and listed end from the newest notice, and records each
    replacement as an update for the timeline.
    """
    by_station = defaultdict(list)
    for o in outages:
        by_station[(o.code, o.kind)].append(o)

    merged = []
    for group in by_station.values():
        group.sort(key=lambda o: (o.first_seen, o.id))
        # Every chain stays open for a successor, not just the most recent one:
        # a second notice still listed at the station (one lift per notice)
        # sorts between a closed notice and its replacement, and comparing only
        # against the last chain would leave that replacement unmerged.
        chains = []
        for o in group:
            for chain in chains:
                prev = chain[-1]
                if not prev.ongoing and o.first_seen == prev.end:
                    chain.append(o)
                    break
            else:
                chains.append([o])
        merged.extend(_fold(chain) for chain in chains)
    merged.sort(key=lambda o: (o.first_seen, o.id), reverse=True)
    return merged


def _fold(chain):
    if len(chain) == 1:
        return chain[0]
    first, last = chain[0], chain[-1]
    return first._replace(
        station=last.station,
        start=min(o.start for o in chain),
        end=last.end,
        ongoing=last.ongoing,
        planned=last.planned,
        listed_end=last.listed_end,
        head=last.head,
        text=last.text,
        updates=tuple((o.first_seen, o.head, o.text) for o in chain[1:]),
        segments=tuple(seg for o in chain for seg in o.segments),
    )


def load_outages(db_path, now):
    """Every lift/escalator notice as an outage, newest first, and the horizon.

    `now` is only used when the run log is empty and there is nothing else to
    end the window at; everything measured stops at the horizon.
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        until = observed_until(conn) or now
        rows = conn.execute(
            """SELECT id, head, text_raw, start_utc, end_utc, location_codes, event_stops,
                      first_seen_at_utc, last_seen_at_utc, status, closed_at_utc
               FROM messages ORDER BY first_seen_at_utc, id"""
        ).fetchall()
    finally:
        conn.close()
    outages = [o for o in (_outage_from_row(r, until) for r in rows) if o is not None]
    return merge_edits(outages), until


def station_index(outages):
    """{code: name}, name taken from the newest notice, ordered by name."""
    names = {}
    for o in sorted(outages, key=lambda o: o.first_seen):
        names[o.code] = o.station
    return dict(sorted(names.items(), key=lambda kv: (kv[1], kv[0])))


def partial_days(until):
    """The days at either end of collection that were watched for only part of.

    Their cells are built from less time than the days beside them, so a lift
    that failed late on the last day reads as a quiet day. The colour still says
    what was seen; these dates let the page say the day was short.
    """
    days = {_local(COLLECTION_START).date(), _local(until - timedelta(microseconds=1)).date()}
    return sorted(d.isoformat() for d in days)


def observed_window(ym, until):
    """The part of month `ym` this site actually watched."""
    lo, hi = month_bounds(ym)
    return max(lo, COLLECTION_START), min(hi, until)


def listed_in(o, lo, hi):
    """Was the notice listed at any point in [lo, hi)?

    Half-open, like every window here, with one exception: a notice first seen
    at the very last poll is listed for zero minutes - `first_seen`, `end` and
    the horizon coincide - and a half-open test would drop it from the month
    it plainly belongs to. It counts in the horizon's month, and nowhere else.
    """
    if o.end <= lo:
        return False
    if o.first_seen < hi:
        return True
    return o.ongoing and o.first_seen == o.end == hi


def _span_days(start, end, lo, hi, ongoing):
    """The Dublin dates covered by [start, end) inside [lo, hi).

    Dublin, not UTC: the outage's own text is rendered in Dublin wall-clock
    (see render._short), so bucketing by UTC date would colour 31 August for a
    notice whose summary says it was first listed at 00:15 on 1 September.
    """
    cur, stop = max(start, lo), min(end, hi)
    if ongoing and cur == stop:
        # Seen at the last poll and never before: on the feed at the horizon,
        # for no measurable time. That is still a listing on that day.
        yield _local(cur).date()
        return
    while cur < stop:
        yield _local(cur).date()
        cur = (_local(cur) + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )


def day_marks(o, lo, hi):
    """(date, planned, counts) per day the notice was listed inside [lo, hi).

    `counts` is False only for a planned-works notice whose whole listing ran
    inside `PLANNED_GRACE` - the whole of it, reissues folded in, not the
    segment the day falls in: works reissued every few days are still works
    that ran for a month, and `merge_edits` exists because Irish Rail reissue.
    It is a property of the notice rather than of the month, too: a fortnight
    of works spanning a month end counts in both halves.
    """
    listed = o.end - o.first_seen
    last = len(o.segments) - 1
    for i, (seg_start, seg_end, seg_planned) in enumerate(o.segments):
        counts = not seg_planned or listed > PLANNED_GRACE
        for day in _span_days(seg_start, seg_end, lo, hi, o.ongoing and i == last):
            yield day, seg_planned, counts


def availability(observed, against):
    """Days available as a whole percent, or None for a month nobody watched.

    Floored, not rounded: 100% has to mean nothing was listed, or the grade
    contradicts the bar beside it.
    """
    if not observed:
        return None
    return (observed - against) * 100 // observed


def grade(avail):
    """The band an availability falls in, or None when there is nothing to grade."""
    if avail is None:
        return None
    return next(letter for floor, letter in GRADE_BANDS if avail >= floor)


def _cells(marks, month_lo, now, until):
    """One kind's day bar for the month, and which of its days were watched."""
    cells, observed = [], set()
    for d in range(1, calendar.monthrange(month_lo.year, month_lo.month)[1] + 1):
        day = date(month_lo.year, month_lo.month, d)
        day_lo = datetime(day.year, day.month, day.day, tzinfo=DUBLIN)
        if day_lo >= now:
            cells.append(DAY_FUTURE)
        elif day_lo + timedelta(days=1) <= COLLECTION_START or day_lo >= until:
            # Either side of the collected window is "no data": a day the
            # collector never reached is not a day the lift worked.
            cells.append(DAY_NO_DATA)
        else:
            cells.append(marks.get(day, DAY_CLEAR))
            observed.add(day)
    return "".join(str(c) for c in cells), observed


def station_month(outages, ym, now, until):
    """Statistics for one station in one month.

    `outages` is the station's full list; the selection happens here so the
    arithmetic and the filter live in one place. `now` decides only what is
    still in the future; everything measured ends at `until`.

    The grade is the lift bar's alone. Step-free access is the lift, and a
    station whose escalator is out while its lifts run should read as what it
    is - the escalator has its own bar to say so.
    """
    lo, hi = observed_window(ym, until)
    month_lo = month_bounds(ym)[0]

    faults = planned = lifts = escalators = 0
    ongoing = False
    marks = {"lift": {}, "escalator": {}}
    against = set()  # lift days that count against availability

    for o in outages:
        if not listed_in(o, lo, hi):
            continue
        if o.planned:
            planned += 1
        else:
            faults += 1
        if o.kind == "lift":
            lifts += 1
        else:
            escalators += 1
        # Only meaningful for the month the horizon falls in, which is the
        # only month an open notice can overlap the end of.
        ongoing = ongoing or (o.ongoing and o.end == hi)

        kind_marks = marks[o.kind]
        for day, day_planned, counts in day_marks(o, lo, hi):
            # a fault beats planned works: the cell says the worst of the day
            if kind_marks.get(day) != DAY_OUT:
                kind_marks[day] = DAY_PLANNED if day_planned else DAY_OUT
            if counts and o.kind == "lift":
                against.add(day)

    cells, observed = _cells(marks["lift"], month_lo, now, until)
    # A day listed but not watched is not a day off the total: the window ends
    # at the horizon, and the bar ends at `now`, which can be the earlier of the
    # two when the collector's clock is ahead of the builder's. Counting those
    # days against a total that excludes them takes availability below zero.
    against &= observed
    # No escalator notice, no escalator bar: an empty second strip on every
    # station would say "no escalator here", which the feed never says.
    esc_cells = _cells(marks["escalator"], month_lo, now, until)[0] if marks["escalator"] else None
    avail = availability(len(observed), len(against))

    return {
        "cells": cells,
        "esc_cells": esc_cells,
        "faults": faults,
        "planned": planned,
        "lifts": lifts,
        "escalators": escalators,
        "observed": len(observed),
        "against": len(against),
        "avail": avail,
        "grade": grade(avail),
        "ongoing": ongoing,
    }


def national_month(outages, ym, now, until):
    """The overview's headline for one month, across every station.

    The availability is aggregated over the stations listed that month, and
    only those: the feed names a station when something is wrong with it, so
    the site has no roll of the stations that have a lift at all, and a
    denominator of "every station" would be invented.
    """
    lo, hi = observed_window(ym, until)
    live = [o for o in outages if listed_in(o, lo, hi)]
    by_code = defaultdict(list)
    for o in live:
        by_code[o.code].append(o)
    # Through station_month, so the headline cannot disagree with the rows.
    per_station = [station_month(rows, ym, now, until) for rows in by_code.values()]
    return {
        "stations": len(by_code),
        "outages": len(live),
        "faults": sum(1 for o in live if not o.planned),
        "planned": sum(1 for o in live if o.planned),
        "avail": availability(
            sum(s["observed"] for s in per_station), sum(s["against"] for s in per_station)
        ),
        "ongoing": len({o.code for o in live if o.ongoing and o.end == hi}),
    }
