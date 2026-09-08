"""Everything the derivation says about a pinned corpus, as one file.

`tests/fixtures/access-golden.json` holds the derivation's inputs and its
outputs side by side, and a test replays the inputs through today's code and
asserts the outputs still match. The point is the diff: a change to a regex or a
sentence that moves a verdict, or a level line, at any of the 152 stations shows
up as a change to a tracked file in the same PR, where a reviewer reads it. Two
such regressions in one day were caught by an ad hoc version of this comparison
and by nothing else in the suite.

The inputs are pinned because the file guards code, and a fixture that re-derives
from live inputs fails on other people's schedules instead. It did, three times:
the notice bodies come from `messages.text_raw`, which the collector overwrites
in place when Irish Rail edits a notice without changing its head or start, so a
reworded banner dropped a pinned key and reddened whatever PR was open. Replaying
pinned inputs also means the test needs no `lifts-data` checkout, so it runs on a
bare clone rather than skipping there unnoticed. `notes/station-access.md`.

The corpus keeps moving; this file catches up when someone runs `golden`, which
adds what the corpus has gained and never drops what is already pinned. Between
regenerations a new notice is covered by the real-corpus checks that need no
file, and a reworded station page by the report `stations.yml` attaches to the
PR it opens against `lifts-data`.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from . import model, snapshot

PATH = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "access-golden.json"


def notices(db_path):
    """Every lift and escalator notice on record, in the form `build` and `report` take.

    Four fields: the station's location code; "lift" or "escalator", which
    `classify` reads off the head; the head, which is the feed's own name for the
    hand-written headline ("Tullamore - Lift out of order"); and the notice body
    as the feed wrote it, which is the form `verdict` takes. `locationCodes[0]`
    is the whole station, every lift notice naming exactly one.

    An empty body is stored as NULL and `verdict` reads None and "" alike, so it
    is "" here: the tuples get sorted, and None will not sort beside a string.
    """
    from lift_site.model import classify

    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT location_codes, head, text_raw FROM messages ORDER BY head"
        ).fetchall()
    finally:
        conn.close()
    out = []
    for codes, head, text in rows:
        kind = classify(head)
        if not kind:
            continue
        try:
            listed = json.loads(codes)
        except json.JSONDecodeError:
            continue
        if listed:
            out.append((listed[0], kind, head, text or ""))
    return out


def _input(station):
    """The payload node `station_from_node` read, as the file pins it.

    A node and not the parsed `Station`, so replaying it goes through the same
    reader a snapshot does and `plain`, `read_platform_access` and
    `station_from_node` are all inside what the file guards.
    """
    return {
        "slug": station.slug,
        "node": {
            "stationCode": station.code,
            "stationName": station.name,
            "platformAccess": {"html": station.platform_access_html},
            "ticketOfficeAccess": {"html": station.ticket_office_access_html},
        },
    }


def build(facts, notices):
    """The derivation's output for every station and every distinct notice."""
    stations = {}
    for code in sorted(facts.stations):
        station = facts.stations[code]
        stations[code] = {
            "input": _input(station),
            "name": station.name,
            "lift_platforms": sorted(station.lift_platforms),
            "claims_lift": station.claims_lift,
            "denies_lift": station.denies_lift,
            "step_free_platforms": [list(pair) for pair in model.step_free_platforms(station)],
            "entrance_lift_sentence": model.entrance_lift_sentence(station),
            "entrance_step_free": model.entrance_step_free(station),
        }
    verdicts = []
    for code, kind, text in sorted({(code, kind, text) for code, kind, _, text in notices}):
        result = facts.verdict(code, kind, text)
        verdicts.append({
            "code": code,
            "kind": kind,
            "text": text,
            "state": result.state,
            "leg": result.leg,
            "platforms": list(result.platforms),
            "detail": result.detail,
        })
    return {
        "snapshot": facts.path.name if facts.path else None,
        "stations": stations,
        "verdicts": verdicts,
    }


def pinned_facts(document):
    """The stations a golden document pinned, read back as `Facts`.

    `snapshot.load` is the other way into this type; the two must agree, so this
    goes through `station_from_node` rather than rebuilding a `Station` here.
    """
    stations = {}
    for pinned in document.get("stations", {}).values():
        source = pinned.get("input") or {}
        station = model.station_from_node(source.get("node") or {}, source.get("slug", ""))
        if station:
            stations[station.code] = station
    return snapshot.Facts(stations)


def pinned_notices(document):
    """The notices a golden document pinned, in the form `build` takes.

    The head is the one field `build` does not read, and the file does not pin
    it, so it comes back empty.
    """
    return [(v["code"], v["kind"], "", v["text"]) for v in document.get("verdicts", [])]


def merge_facts(pinned, live):
    """`live` over `pinned`, so a regeneration adds and updates but never drops.

    A station the snapshot no longer carries keeps the prose it was pinned with,
    which is what makes its verdicts stay reproducible.
    """
    stations = dict(pinned.stations)
    stations.update(live.stations)
    return snapshot.Facts(stations, live.path or pinned.path, live.dropped)


def _key(verdict):
    return verdict["code"], verdict["kind"], verdict["text"]


def _moved(label, before, after):
    return [
        f"{label}: {field}: {before.get(field)!r} -> {after.get(field)!r}"
        for field in sorted(set(before) | set(after))
        if before.get(field) != after.get(field)
    ]


def differences(stored, current):
    """Where two golden documents disagree about something both describe.

    Moves only. What each document holds and the other does not is the size of
    the corpus, which no code change decides: `stations.yml` and the collector do,
    on their own schedules, and a guard that failed on that was red for reasons no
    PR caused. `snapshot` goes the same way, recorded as provenance and not
    compared. `new_notices` is how a regeneration reports what it gained.
    """
    out = []
    old_stations, new_stations = stored.get("stations", {}), current.get("stations", {})
    for code in sorted(set(old_stations) & set(new_stations)):
        out.extend(_moved(f"station {code}", old_stations[code], new_stations[code]))
    old_verdicts = {_key(v): v for v in stored.get("verdicts", [])}
    new_verdicts = {_key(v): v for v in current.get("verdicts", [])}
    for k in sorted(set(old_verdicts) & set(new_verdicts)):
        out.extend(_moved(f"notice {k[0]} {k[1]}", old_verdicts[k], new_verdicts[k]))
    return out


def new_notices(stored, current):
    """The notices `current` holds that `stored` has not pinned yet."""
    seen = {_key(v) for v in stored.get("verdicts", [])}
    return [v for v in current.get("verdicts", []) if _key(v) not in seen]


def dumps(document):
    return json.dumps(document, indent=1, sort_keys=True, ensure_ascii=False) + "\n"


GRAPH_PATH = PATH.with_name("graph-golden.json")


def build_graph(facts, survey_data, notices, fingerprint):
    """What the survey-derived graphs say, for the surveyed stations and their notices.

    Its own file, keyed on the survey files' fingerprint and not on the station
    snapshot: a survey append must not fail the station golden, a refreshed
    snapshot must not fail this one by name alone (a page quote that expired
    with it still fails it, on the fact that went), and the station golden must
    not move when a survey line lands. Same document shape as `build`, so
    `differences`, `new_notices` and `dumps` apply unchanged.
    """
    from . import graph as graph_module

    stations, verdicts = {}, []
    graphs = {}
    for code in sorted(survey_data.observations):
        station = facts.station(code) if facts else None
        observations = survey_data.observations[code]
        graph, problems = graph_module.replay(observations, station)
        graphs[code] = graph
        reached = graph_module.step_free_platforms(graph)
        stations[code] = {
            "name": station.name if station else None,
            "observations": len(observations),
            "complete": graph.complete,
            "problems": problems,
            "contradictions": graph_module.contradictions(graph, station),
            "step_free_platforms": {
                label: graph_module.describe_route(graph, route) for label, route in reached.items()
            },
            "lift_platforms": list(graph_module.lift_platforms(graph)),
            "never": [label for label in graph.platforms() if label not in reached],
        }
    for code, kind, text in sorted({(code, kind, text) for code, kind, _, text in notices}):
        if code not in graphs:
            continue
        result = graph_module.verdict(graphs[code], kind, text)
        verdicts.append({
            "code": code,
            "kind": kind,
            "text": text,
            "state": result.state,
            "leg": result.leg,
            "platforms": list(result.platforms),
            "detail": result.detail,
        })
    return {
        "snapshot": f"survey@{fingerprint}",
        "stations": stations,
        "verdicts": verdicts,
    }
