"""Everything the derivation says about the checked-out corpus, as one file.

`tests/fixtures/access-golden.json` is regenerated from the snapshot and the
database, and a real-corpus test asserts the regeneration matches. The point is
the diff: a change to a regex or a sentence that moves a verdict, or a level
line, at any of the 152 stations shows up as a change to a tracked file in the
same PR, where a reviewer reads it. Two such regressions in one day were caught
by an ad hoc version of this comparison and by nothing else in the suite.

The file names the snapshot it was built from. A refreshed snapshot fails the
test until the file is regenerated, which is the monthly report made mandatory:
a reworded station page becomes a diff that has to be read before it lands.

A notice the file has never seen is not a failure. The corpus gains one every
few days and CI reads it at its head, so a guard that failed on new data would
be red most of the time for reasons no PR caused. New notices are pinned at the
next regeneration, and until then the other real-corpus tests cover them.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from . import model

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


def build(facts, notices):
    """The derivation's output for every station and every distinct notice."""
    stations = {}
    for code in sorted(facts.stations):
        station = facts.stations[code]
        stations[code] = {
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


def _key(verdict):
    return verdict["code"], verdict["kind"], verdict["text"]


def _moved(label, before, after):
    return [
        f"{label}: {field}: {before.get(field)!r} -> {after.get(field)!r}"
        for field in sorted(set(before) | set(after))
        if before.get(field) != after.get(field)
    ]


def differences(stored, current):
    """Where two golden documents disagree, one line each, for a test message.

    A notice only `current` holds is not a disagreement: the file pins what the
    derivation says about the notices it has, not the size of the corpus.
    """
    out = []
    if stored.get("snapshot") != current.get("snapshot"):
        out.append(f"snapshot: {stored.get('snapshot')} -> {current.get('snapshot')}")
    old_stations, new_stations = stored.get("stations", {}), current.get("stations", {})
    for code in sorted(set(old_stations) | set(new_stations)):
        before, after = old_stations.get(code), new_stations.get(code)
        if before is None or after is None:
            out.append(f"station {code}: {'added' if before is None else 'dropped'}")
            continue
        out.extend(_moved(f"station {code}", before, after))
    old_verdicts = {_key(v): v for v in stored.get("verdicts", [])}
    new_verdicts = {_key(v): v for v in current.get("verdicts", [])}
    for k in sorted(old_verdicts):
        before, after = old_verdicts[k], new_verdicts.get(k)
        if after is None:
            out.append(f"notice {k[0]} {k[1]}: dropped")
            continue
        out.extend(_moved(f"notice {k[0]} {k[1]}", before, after))
    return out


def new_notices(stored, current):
    """The notices `current` holds that `stored` has not pinned yet."""
    seen = {_key(v) for v in stored.get("verdicts", [])}
    return [v for v in current.get("verdicts", []) if _key(v) not in seen]


def dumps(document):
    return json.dumps(document, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
