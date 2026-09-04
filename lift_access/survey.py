"""The observation log: what somebody recorded about a station, with provenance.

`notes/accessible-routes.md` rejected a hand-maintained station file for three
reasons: no provenance, no refresh, no audit. This is the answer to all three
and it is shaped like the raw JSONL logs for the same reason they are: one
observation per line, never edited, every line saying who recorded it, when and
from what. A correction is a later line with the same fact id, and `graph.replay`
applies the file in order with the last line for a key winning, exactly as
`rebuild` replays the collector's logs. `notes/step-free-graph.md`.

Nothing here decides what is true. This module says what a line may look like
and reads the files back; the graph module says what the lines add up to.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import NamedTuple

SURVEY_DIR = "survey"

# Low is read off a page by nobody who has stood in the station; medium is a
# reviewed sentence or something a person was told; high is something a person
# saw. The graph publishes "another step-free way" only on medium or better.
CONFIDENCE = ("low", "medium", "high")

# What each kind of source has to carry so the line can be audited later. A
# page quote is verbatim and expires with the page; a survey names a person; a
# support answer or FOI has a reference; imagery has a URL and OSM an object.
SOURCE_KINDS = {
    "irishrail-page": ("snapshot", "field", "quote"),
    "survey": ("by",),
    "irishrail-support": ("reference",),
    "nta-pbc-2024-10": ("page",),
    "photo": ("file",),
    "imagery": ("url",),
    "osm": ("object", "date"),
    "foi": ("reference",),
}
PAGE_FIELDS = ("platformAccess", "ticketOfficeAccess")

FACT_TYPES = ("level", "node", "edge", "equipment", "retract", "note")
KEYED_TYPES = ("level", "node", "edge", "equipment")
NODE_KINDS = ("entrance", "concourse", "platform", "landing", "generic")
# `unsurveyed` is a way known to exist whose nature nobody has recorded. Without
# it an entrance the seeder cannot read would make every platform "never
# step-free"; with it the graph is incomplete, which is the truth.
MODES = (
    "walkway", "ramp", "stairs", "footbridge-stairs", "subway-stairs",
    "lift", "escalator", "gate", "unsurveyed",
)
STEP_FREE_MODES = frozenset({"walkway", "ramp", "lift", "gate"})
GATE_KINDS = ("wicket", "barrow-crossing", "level-crossing", "ticket-barrier")
EQUIPMENT_KINDS = ("lift", "escalator")
EQUIPMENT_MODES = frozenset({"lift", "escalator"})

ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CODE = re.compile(r"^[A-Z0-9]{2,8}$")


class Observation(NamedTuple):
    code: str
    observed: str
    confidence: str
    source: dict
    fact: dict
    note: str | None
    line: int  # 1-based line in its file, for messages


class Survey(NamedTuple):
    observations: dict  # code -> observations in file order
    problems: list  # "path:line: why", for lines that were skipped
    path: Path | None

    def __bool__(self):
        return bool(self.observations)


def _check(errors, condition, message):
    if not condition:
        errors.append(message)
    return bool(condition)


def _optional(errors, fact, field, types, what):
    value = fact.get(field)
    if value is not None and not isinstance(value, types):
        errors.append(f"fact.{field} must be {what}")


def _validate_fact(fact, errors):
    if not _check(errors, isinstance(fact, dict), "fact must be an object"):
        return
    kind = fact.get("type")
    if not _check(errors, kind in FACT_TYPES, f"fact.type must be one of {', '.join(FACT_TYPES)}"):
        return
    if kind == "note":
        _check(errors, isinstance(fact.get("text"), str) and fact["text"].strip(),
               "a note needs text")
        return
    ident = fact.get("id")
    _check(errors, isinstance(ident, str) and ID.match(ident),
           "fact.id must be lower-case letters, digits and hyphens")
    if kind == "retract":
        _check(errors, fact.get("of") in KEYED_TYPES,
               f"retract.of must be one of {', '.join(KEYED_TYPES)}")
        return
    if kind == "level":
        _check(errors, isinstance(fact.get("index"), int) and not isinstance(fact["index"], bool),
               "a level needs an integer index")
        _optional(errors, fact, "name", str, "text")
        return
    if kind == "node":
        node_kind = fact.get("kind")
        _check(errors, node_kind in NODE_KINDS,
               f"node.kind must be one of {', '.join(NODE_KINDS)}")
        if node_kind == "platform":
            _check(errors, isinstance(fact.get("platform"), str) and fact["platform"].strip(),
                   "a platform node needs its platform label")
        _optional(errors, fact, "name", str, "text")
        _optional(errors, fact, "level", str, "a level id")
        return
    if kind == "equipment":
        _check(errors, fact.get("kind") in EQUIPMENT_KINDS,
               f"equipment.kind must be one of {', '.join(EQUIPMENT_KINDS)}")
        _optional(errors, fact, "name", str, "text")
        _optional(errors, fact, "hours", str, "text")
        _optional(errors, fact, "call", bool, "true or false")
        for field in ("landings", "aliases"):
            value = fact.get(field)
            if value is not None and not (
                isinstance(value, list) and all(isinstance(v, str) for v in value)
            ):
                errors.append(f"equipment.{field} must be a list of strings")
        return
    # edge
    mode = fact.get("mode")
    _check(errors, mode in MODES, f"edge.mode must be one of {', '.join(MODES)}")
    for end in ("from", "to"):
        _check(errors, isinstance(fact.get(end), str) and ID.match(fact.get(end) or ""),
               f"edge.{end} must be a node id")
    if mode == "gate":
        _check(errors, fact.get("gate") in GATE_KINDS,
               f"a gate edge needs gate, one of {', '.join(GATE_KINDS)}")
    if mode in EQUIPMENT_MODES:
        equipment = fact.get("equipment")
        _check(errors, isinstance(equipment, str) and ID.match(equipment),
               f"a {mode} edge needs the equipment id it belongs to")
    _optional(errors, fact, "bidirectional", bool, "true or false")
    _optional(errors, fact, "wheelchair", bool, "true or false")
    _optional(errors, fact, "hours", str, "text")
    _optional(errors, fact, "stair_count", int, "an integer")
    _optional(errors, fact, "slope", (int, float), "a number")
    _optional(errors, fact, "width", (int, float), "a number")


def validate(obj, expected_code=None):
    """Everything wrong with one observation, as messages; empty when it is fine."""
    errors = []
    if not _check(errors, isinstance(obj, dict), "an observation is a JSON object"):
        return errors
    code = obj.get("code")
    if _check(errors, isinstance(code, str) and CODE.match(code), "code must be a station code"):
        if expected_code is not None:
            _check(errors, code == expected_code,
                   f"code {code} in a file for {expected_code}")
    observed = obj.get("observed")
    _check(errors, isinstance(observed, str) and DATE.match(observed),
           "observed must be a YYYY-MM-DD date")
    _check(errors, obj.get("confidence") in CONFIDENCE,
           f"confidence must be one of {', '.join(CONFIDENCE)}")
    source = obj.get("source")
    if _check(errors, isinstance(source, dict), "source must be an object"):
        kind = source.get("kind")
        if _check(errors, kind in SOURCE_KINDS,
                  f"source.kind must be one of {', '.join(SOURCE_KINDS)}"):
            for field in SOURCE_KINDS[kind]:
                value = source.get(field)
                # An empty page quote is allowed and means the field said nothing
                # usable; it expires when the field starts saying something.
                blank_ok = kind == "irishrail-page" and field == "quote"
                _check(errors, isinstance(value, (str, int)) and (str(value).strip() or blank_ok),
                       f"a {kind} source needs {field}")
            if kind == "irishrail-page":
                _check(errors, source.get("field") in PAGE_FIELDS,
                       f"source.field must be one of {', '.join(PAGE_FIELDS)}")
    note = obj.get("note")
    if note is not None:
        _check(errors, isinstance(note, str), "note must be text")
    _validate_fact(obj.get("fact"), errors)
    return errors


def observation(obj, line=0):
    return Observation(
        code=obj["code"],
        observed=obj["observed"],
        confidence=obj["confidence"],
        source=obj["source"],
        fact=obj["fact"],
        note=obj.get("note"),
        line=line,
    )


def dumps(obj):
    """One observation as one line, keys sorted so two logs merge with sort -u."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n"


def read(path, expected_code=None):
    """(observations, problems) from one file. A bad line is skipped, and said."""
    found, problems = [], []
    with open(path, encoding="utf-8") as handle:
        for number, raw in enumerate(handle, 1):
            if not raw.strip():
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError as exc:
                problems.append(f"{path}:{number}: not JSON ({exc.msg})")
                continue
            errors = validate(obj, expected_code)
            if errors:
                problems.append(f"{path}:{number}: " + "; ".join(errors))
                continue
            found.append(observation(obj, number))
    return found, problems


def load(data_dir):
    """Every station's log under <data_dir>/survey, in file order."""
    directory = Path(data_dir) / SURVEY_DIR
    if not directory.is_dir():
        return Survey({}, [], None)
    observations, problems = {}, []
    for path in sorted(directory.glob("*.jsonl")):
        code = path.stem
        found, wrong = read(path, code)
        problems.extend(wrong)
        if found or not wrong:
            observations[code] = found
    return Survey(observations, problems, directory)


def digest(data_dir):
    """A short fingerprint of the survey files, so a fixture can name what it pinned."""
    directory = Path(data_dir) / SURVEY_DIR
    hasher = hashlib.sha256()
    if directory.is_dir():
        for path in sorted(directory.glob("*.jsonl")):
            hasher.update(path.name.encode("utf-8"))
            hasher.update(path.read_bytes())
    return hasher.hexdigest()[:12]
