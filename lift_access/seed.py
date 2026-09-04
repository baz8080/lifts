"""Draft observations for a station, read off Irish Rail's page, for a person to correct.

A questionnaire that starts blank gets answered slowly; one that starts with
"the page says this, is it right" gets answered. Every line here is a claim
the page already makes, quoted, at low confidence, so the graph it seeds can
never say more than the prose derivation does (`graph.CONFIRMED`). It uses the
same pickers as `model.py`, so a sentence that moves there moves here, and it
parses no connectives: "lifts and ramps" gives a lift edge and no ramp edge.

The same page, seeded twice, gives the same lines: `observed` is the
snapshot's date, not today's, so a reseed is byte-identical and a diff shows
only what the page changed.
"""

from __future__ import annotations

import re

from . import model, survey

STAIRS = re.compile(r"\b(?:stair\w*|steps?|footbridge|subway)\b", re.IGNORECASE)
RAMP = re.compile(r"\bramps?\b", re.IGNORECASE)

ENTRANCE = "entrance"
CONCOURSE = "concourse"
SECOND_ENTRANCE = "entrance-2"


def observed_date(snapshot_name):
    """'irishrail-20260901.jsonl' -> '2026-09-01'."""
    match = re.search(r"(\d{4})(\d{2})(\d{2})", snapshot_name or "")
    if not match:
        raise ValueError(f"no date in snapshot name {snapshot_name!r}")
    return "-".join(match.groups())


def _stairs_mode(sentence):
    lowered = sentence.lower()
    if "footbridge" in lowered:
        return "footbridge-stairs"
    if "subway" in lowered:
        return "subway-stairs"
    return "stairs"


class _Seeder:
    def __init__(self, station, snapshot_name):
        self.station = station
        self.snapshot = snapshot_name
        self.observed = observed_date(snapshot_name)
        self.nodes, self.equipment, self.edges, self.notes = {}, {}, {}, []

    def source(self, field, quote, reviewed=None):
        out = {"kind": "irishrail-page", "snapshot": self.snapshot, "field": field,
               "quote": quote}
        if reviewed:
            out["reviewed"] = reviewed
        return out

    def line(self, fact, field, quote, confidence="low", reviewed=None):
        return {
            "code": self.station.code,
            "observed": self.observed,
            "confidence": confidence,
            "source": self.source(field, quote, reviewed),
            "fact": fact,
        }

    def node(self, ident, kind, field, quote, **extra):
        if ident not in self.nodes:
            fact = {"type": "node", "id": ident, "kind": kind, **extra}
            self.nodes[ident] = self.line(fact, field, quote)

    def platform(self, label, field, quote):
        ident = f"platform-{label.lower()}"
        self.node(ident, "platform", field, quote, platform=label)
        return ident

    def machine(self, ident, kind, field, quote):
        if ident not in self.equipment:
            self.equipment[ident] = self.line(
                {"type": "equipment", "id": ident, "kind": kind}, field, quote
            )

    def edge(self, ident, mode, start, end, field, quote, confidence="low", reviewed=None,
             **extra):
        if ident in self.edges:
            return
        fact = {"type": "edge", "id": ident, "mode": mode, "from": start, "to": end, **extra}
        self.edges[ident] = self.line(fact, field, quote, confidence, reviewed)

    def note(self, text, field, quote):
        self.notes.append(self.line({"type": "note", "text": text}, field, quote))

    def entrance_leg(self):
        field = "ticketOfficeAccess"
        entry = self.station.ticket_office_access or ""
        lift = model.lift_sentence(entry)
        level = model.entrance_step_free(self.station)
        first = model._sentences(entry)
        self.node(ENTRANCE, "entrance", field, first[0] if first else "",
                  name="the station entrance")
        if lift:
            self.machine("lift-entrance", "lift", field, lift)
            self.edge("lift-entrance", "lift", ENTRANCE, CONCOURSE, field, lift,
                      equipment="lift-entrance")
            if STAIRS.search(lift):
                self.edge("stairs-entrance", _stairs_mode(lift), ENTRANCE, CONCOURSE, field, lift)
            if model.ESCALATOR.search(lift):
                self.machine("escalator-entrance", "escalator", field, lift)
                self.edge("escalator-entrance", "escalator", ENTRANCE, CONCOURSE, field, lift,
                          equipment="escalator-entrance")
        if level:
            self.edge("way-in", "ramp" if RAMP.search(level) else "walkway", ENTRANCE, CONCOURSE,
                      field, level)
        if not lift and not level:
            # "No ticket office", "Not level", or nothing at all: the page says
            # nothing usable about the door, and the graph must say so rather
            # than make every platform unreachable.
            self.edge("way-in", "unsurveyed", ENTRANCE, CONCOURSE, field,
                      first[0] if first else "")

    def platform_leg(self):
        station, field = self.station, "platformAccess"
        prose = station.platform_access or ""
        sentences = model._sentences(prose)
        self.node(CONCOURSE, "concourse", field, sentences[0] if sentences else "",
                  name="the concourse or ticket office")
        for label, sentence in model.step_free_platforms(station):
            node = self.platform(label, field, sentence)
            self.edge(f"level-p{label.lower()}", "ramp" if RAMP.search(sentence) else "walkway",
                      CONCOURSE, node, field, sentence)
        for sentence in sentences:
            has_lift = bool(model.LIFT.search(sentence)) and not model.DENIES_LIFT.search(sentence)
            has_escalator = bool(model.ESCALATOR.search(sentence))
            stairs = bool(STAIRS.search(sentence))
            named = model.platforms_named(sentence)
            if (
                model.FROM_PLATFORM.search(sentence) and model.STEP_FREE.search(sentence)
                and not stairs and not has_lift and len(named) == 2
            ):
                a, b = (self.platform(p, field, sentence) for p in named)
                self.edge(f"link-p{named[0].lower()}-p{named[1].lower()}",
                          "ramp" if RAMP.search(sentence) else "walkway", a, b, field, sentence)
                continue
            if has_lift:
                if named:
                    for label in named:
                        node = self.platform(label, field, sentence)
                        ident = f"lift-p{label.lower()}"
                        self.machine(ident, "lift", field, sentence)
                        self.edge(ident, "lift", CONCOURSE, node, field, sentence, equipment=ident)
                        if stairs:
                            self.edge(f"stairs-p{label.lower()}", _stairs_mode(sentence),
                                      CONCOURSE, node, field, sentence)
                        if has_escalator:
                            esc = f"escalator-p{label.lower()}"
                            self.machine(esc, "escalator", field, sentence)
                            self.edge(esc, "escalator", CONCOURSE, node, field, sentence,
                                      equipment=esc)
                elif model.leg_named(sentence) == model.ENTRANCE_LEG:
                    self.node(SECOND_ENTRANCE, "entrance", field, sentence,
                              name="the entrance the page names beside the platforms")
                    self.machine("lift-entrance-2", "lift", field, sentence)
                    self.edge("lift-entrance-2", "lift", SECOND_ENTRANCE, CONCOURSE, field,
                              sentence, equipment="lift-entrance-2")
                    if stairs:
                        self.edge("stairs-entrance-2", _stairs_mode(sentence), SECOND_ENTRANCE,
                                  CONCOURSE, field, sentence)
                    if has_escalator:
                        self.machine("escalator-entrance-2", "escalator", field, sentence)
                        self.edge("escalator-entrance-2", "escalator", SECOND_ENTRANCE,
                                  CONCOURSE, field, sentence, equipment="escalator-entrance-2")
                elif model.ALL_PLATFORMS in station.lift_platforms:
                    self.note(
                        "The page claims a lift without saying which platform it serves, so "
                        "no lift is drawn: which platforms does it reach?", field, sentence,
                    )
                continue
            if named and has_escalator:
                for label in named:
                    node = self.platform(label, field, sentence)
                    esc = f"escalator-p{label.lower()}"
                    self.machine(esc, "escalator", field, sentence)
                    self.edge(esc, "escalator", CONCOURSE, node, field, sentence, equipment=esc)
            if named and stairs:
                for label in named:
                    node = self.platform(label, field, sentence)
                    self.edge(f"stairs-p{label.lower()}", _stairs_mode(sentence), CONCOURSE, node,
                              field, sentence)
        # The two reviewed step-free alternatives, at medium: a person read them.
        for (code, label), quoted in model.STEP_FREE_ALTERNATIVES.items():
            if code == station.code and model._alternative(station, label):
                node = self.platform(label, field, quoted)
                self.edge(f"ramp-p{label.lower()}", "ramp", CONCOURSE, node, field, quoted,
                          confidence="medium", reviewed="STEP_FREE_ALTERNATIVES")

    def lines(self):
        self.platform_leg()
        self.entrance_leg()
        ordered = [self.nodes[ENTRANCE]]
        if SECOND_ENTRANCE in self.nodes:
            ordered.append(self.nodes[SECOND_ENTRANCE])
        ordered.append(self.nodes[CONCOURSE])
        ordered.extend(
            line for ident, line in sorted(self.nodes.items())
            if ident not in (ENTRANCE, SECOND_ENTRANCE, CONCOURSE)
        )
        ordered.extend(line for _, line in sorted(self.equipment.items()))
        ordered.extend(line for _, line in sorted(self.edges.items()))
        ordered.extend(self.notes)
        return ordered


def observations(station, snapshot_name):
    """Every draft line for one station, in a stable order, each valid."""
    lines = _Seeder(station, snapshot_name).lines()
    for line in lines:
        errors = survey.validate(line, station.code)
        if errors:  # a seeder bug, not a data problem: fail loudly
            raise AssertionError(f"seed for {station.code} produced an invalid line: {errors}")
    return lines


def dumps(lines):
    return "".join(survey.dumps(line) for line in lines)
