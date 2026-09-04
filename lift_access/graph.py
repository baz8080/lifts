"""A station as a graph, replayed from its observation log, and what a notice does to it.

The prose derivation in `model.py` reads Irish Rail's sentences and assumes a
lift out removes step-free access to the platforms it serves, because it cannot
see the station. This module can, once somebody has recorded it: entrances,
platforms and the ways between them, each way typed, each fact carrying who
recorded it and how sure they were. "Is platform 2 still reachable without
steps when this lift is out" is then a reachability question, answered by
removing the lift's edges and looking, instead of a sentence pattern.

Two rules keep it on the safe side of `notes/station-access.md` § The safe
direction. The graph says "another step-free way" only where every edge on
the surviving route was recorded at medium confidence or better, so a graph
seeded from the page alone can never say more than the page does. And a notice
that matches no recorded equipment is `unknown`, never a guess.
"""

from __future__ import annotations

import heapq
from typing import NamedTuple

from . import model, survey

CONFIRMED = frozenset({"medium", "high"})
STATES = ("lost", "alternative", "escalator", "unknown")


class Level(NamedTuple):
    id: str
    index: int
    name: str | None
    observed: str
    source: dict
    confidence: str


class Node(NamedTuple):
    id: str
    kind: str
    name: str | None
    platform: str | None
    level: str | None
    observed: str
    source: dict
    confidence: str


class Edge(NamedTuple):
    id: str
    mode: str
    start: str
    end: str
    bidirectional: bool
    gate: str | None
    stair_count: int | None
    slope: float | None
    width: float | None
    hours: str | None
    wheelchair: bool | None
    equipment: str | None
    observed: str
    source: dict
    confidence: str


class Equipment(NamedTuple):
    id: str
    kind: str
    name: str | None
    landings: tuple
    hours: str | None
    call: bool | None
    aliases: tuple
    observed: str
    source: dict
    confidence: str


class StationGraph(NamedTuple):
    code: str
    levels: dict
    nodes: dict
    edges: dict
    equipment: dict
    notes: tuple  # (text, observation) pairs
    complete: bool  # no edge is `unsurveyed`

    def __bool__(self):
        return bool(self.nodes)

    def platforms(self):
        """label -> node id, in label order."""
        found = {n.platform: n.id for n in self.nodes.values() if n.kind == "platform"}
        return dict(sorted(found.items(), key=lambda item: _label_key(item[0])))

    def entrances(self):
        return tuple(n.id for n in self.nodes.values() if n.kind == "entrance")

    def edges_of(self, equipment_id):
        return tuple(e.id for e in self.edges.values() if e.equipment == equipment_id)


def _label_key(label):
    digits = "".join(ch for ch in label if ch.isdigit())
    return (int(digits) if digits else 0, label)


def _quote_gone(observation, station):
    """A page fact whose quoted sentence has left the page no longer describes it.

    An empty quote recorded that the field said nothing usable (blank, or
    boilerplate only), and it is gone the day the field says something.
    """
    source = observation.source
    if station is None or source.get("kind") != "irishrail-page":
        return False
    field = source.get("field")
    prose = station.platform_access if field == "platformAccess" else station.ticket_office_access
    quote = " ".join(str(source.get("quote", "")).split())
    if not quote:
        return bool(model._sentences(prose))
    return quote not in " ".join((prose or "").split())


def replay(observations, station=None):
    """(StationGraph, problems): the log applied in order, last line for a key winning.

    With `station` given, a page-sourced fact whose quote is no longer on the
    page is dropped and reported: the `STEP_FREE_ALTERNATIVES` rule, generalised.
    """
    levels, nodes, edges, equipment, notes, problems = {}, {}, {}, {}, [], []
    stores = {"level": levels, "node": nodes, "edge": edges, "equipment": equipment}
    code = observations[0].code if observations else ""
    for obs in observations:
        fact = obs.fact
        kind = fact["type"]
        if kind == "note":
            notes.append((fact["text"], obs))
            continue
        if kind == "retract":
            if stores[fact["of"]].pop(fact["id"], None) is None:
                problems.append(f"line {obs.line}: retracts {fact['of']} {fact['id']}, "
                                "which the log had not recorded")
            continue
        if _quote_gone(obs, station):
            problems.append(
                f"line {obs.line}: dropped {kind} {fact['id']}, its quoted sentence "
                f"is no longer in {obs.source.get('field')} on Irish Rail's page"
            )
            continue
        common = (obs.observed, obs.source, obs.confidence)
        if kind == "level":
            levels[fact["id"]] = Level(fact["id"], fact["index"], fact.get("name"), *common)
        elif kind == "node":
            nodes[fact["id"]] = Node(
                fact["id"], fact["kind"], fact.get("name"), fact.get("platform"),
                fact.get("level"), *common,
            )
        elif kind == "equipment":
            equipment[fact["id"]] = Equipment(
                fact["id"], fact["kind"], fact.get("name"), tuple(fact.get("landings") or ()),
                fact.get("hours"), fact.get("call"), tuple(fact.get("aliases") or ()), *common,
            )
        else:
            edges[fact["id"]] = Edge(
                fact["id"], fact["mode"], fact["from"], fact["to"],
                fact.get("bidirectional", True), fact.get("gate"), fact.get("stair_count"),
                fact.get("slope"), fact.get("width"), fact.get("hours"), fact.get("wheelchair"),
                fact.get("equipment"), *common,
            )
    for edge in edges.values():
        for end in (edge.start, edge.end):
            if end not in nodes:
                problems.append(f"edge {edge.id} touches node {end}, which is not recorded")
        if edge.equipment is not None:
            item = equipment.get(edge.equipment)
            if item is None:
                problems.append(f"edge {edge.id} belongs to equipment {edge.equipment}, "
                                "which is not recorded")
            elif item.kind != edge.mode:
                problems.append(f"edge {edge.id} is a {edge.mode} but {edge.equipment} "
                                f"is a {item.kind}")
    for node in nodes.values():
        if node.level is not None and node.level not in levels:
            problems.append(f"node {node.id} is on level {node.level}, which is not recorded")
    complete = not any(e.mode == "unsurveyed" for e in edges.values())
    return StationGraph(code, levels, nodes, edges, equipment, tuple(notes), complete), problems


def step_free(edge):
    return edge.mode in survey.STEP_FREE_MODES and edge.wheelchair is not False


def _neighbours(graph, removed, confirmed_only):
    """node id -> [(node id, edge)] over the step-free edges still in play."""
    out = {node: [] for node in graph.nodes}
    for edge in graph.edges.values():
        if edge.id in removed or not step_free(edge):
            continue
        if confirmed_only and edge.confidence not in CONFIRMED:
            continue
        if edge.start not in out or edge.end not in out:
            continue
        out[edge.start].append((edge.end, edge))
        if edge.bidirectional:
            out[edge.end].append((edge.start, edge))
    return out


def routes(graph, removed=frozenset(), confirmed_only=False):
    """node id -> the edges of one step-free route from an entrance, for every node reached.

    The route with the fewest lifts wins, then the fewest edges: Connolly's way
    in has a lift, an escalator, stairs and a level walk from the car park side
    by side, and the one to describe is the one that needs no machine.
    """
    neighbours = _neighbours(graph, removed, confirmed_only)
    best = {}
    heap = [((0, 0), start, ()) for start in sorted(graph.entrances())]
    heapq.heapify(heap)
    while heap:
        cost, here, path = heapq.heappop(heap)
        if here in best:
            continue
        best[here] = path
        for there, edge in neighbours[here]:
            if there not in best:
                step = (cost[0] + (edge.mode == "lift"), cost[1] + 1)
                heapq.heappush(heap, (step, there, path + (edge.id,)))
    return best


def reachable(graph, removed=frozenset()):
    return frozenset(routes(graph, removed))


def _served(graph, removed, before):
    """Platform nodes the removed edges served: touched directly, or on the best route."""
    touched = set()
    for edge_id in removed:
        edge = graph.edges[edge_id]
        for end in (edge.start, edge.end):
            node = graph.nodes.get(end)
            if node is not None and node.kind == "platform":
                touched.add(end)
    for node, route in before.items():
        if graph.nodes[node].kind == "platform" and any(e in removed for e in route):
            touched.add(node)
    return frozenset(touched)


def step_free_platforms(graph):
    """label -> route (edge ids) for every platform reachable without steps."""
    found = routes(graph)
    return {label: found[node] for label, node in graph.platforms().items() if node in found}


def lift_platforms(graph):
    """Labels of the platforms a lift edge touches."""
    ids = {n.id: n.platform for n in graph.nodes.values() if n.kind == "platform"}
    out = set()
    for edge in graph.edges.values():
        if edge.mode == "lift":
            out.update(label for node, label in ids.items() if node in (edge.start, edge.end))
    return tuple(sorted(out, key=_label_key))


class Outcome(NamedTuple):
    joined: tuple  # equipment ids the notice was read as
    removed: tuple  # their edges
    lost: tuple  # platforms with no step-free route left
    alternative: tuple  # platforms kept by a route recorded at medium or better
    unconfirmed: tuple  # platforms kept only by a route nobody has confirmed
    unaffected: tuple  # platforms whose routes never used the equipment
    never: tuple  # platforms with no step-free route before either
    unmatched: tuple  # platforms the notice named that no equipment touches


def join_notice(graph, kind, text):
    """(equipment ids, unmatched platform labels) for the machine a notice names.

    By alias first, then by the platform the notice names, then by the leg: an
    entrance-leg notice is every machine touching an entrance, and a notice that
    names nowhere is every machine of its kind. A platform the notice names that
    no equipment touches is returned rather than guessed at.
    """
    body = model.plain(text).lower() if text else ""
    named = model.affected_platforms(text)
    leg = model.leg_named(text)
    platform_nodes = graph.platforms()
    candidates = [e for e in graph.equipment.values() if e.kind == kind]
    joined, unmatched = [], []
    for item in candidates:
        if any(alias.lower() in body for alias in item.aliases if alias):
            joined.append(item.id)
    if named:
        for label in named:
            node = platform_nodes.get(label)
            hits = [
                item.id for item in candidates
                if node is not None and any(
                    node in (graph.edges[e].start, graph.edges[e].end)
                    for e in graph.edges_of(item.id)
                )
            ]
            if hits:
                joined.extend(h for h in hits if h not in joined)
            elif not joined:
                unmatched.append(label)
    elif leg == model.ENTRANCE_LEG:
        entrances = set(graph.entrances())
        for item in candidates:
            if item.id not in joined and any(
                graph.edges[e].start in entrances or graph.edges[e].end in entrances
                for e in graph.edges_of(item.id)
            ):
                joined.append(item.id)
    elif not joined:
        joined = [item.id for item in candidates]
    return tuple(joined), tuple(unmatched)


def outcome(graph, kind, text):
    """Which platforms a notice's equipment took the step-free way from, and which it did not.

    Served means the equipment's own edge reaches the platform, or the best
    route to it ran through the equipment, or the platform drops out of reach
    without it. A served platform that stays reachable is kept: by a confirmed
    route, or by one nobody has checked, which the verdict counts as lost.
    """
    joined, unmatched = join_notice(graph, kind, text)
    removed = frozenset(e for item in joined for e in graph.edges_of(item))
    platforms = graph.platforms()
    best = routes(graph)
    before = frozenset(best)
    after = reachable(graph, removed)
    touched = _served(graph, removed, best)
    confirmed = frozenset(routes(graph, removed, True))
    lost, alternative, unconfirmed, unaffected, never = [], [], [], [], []
    for label, node in platforms.items():
        if node not in before:
            never.append(label)
        elif node not in after:
            lost.append(label)
        elif node in touched:
            (alternative if node in confirmed else unconfirmed).append(label)
        else:
            unaffected.append(label)
    return Outcome(
        joined, tuple(sorted(removed)), tuple(lost), tuple(alternative), tuple(unconfirmed),
        tuple(unaffected), tuple(never), unmatched,
    )


def describe(graph, node_id):
    node = graph.nodes.get(node_id)
    if node is None:
        return node_id
    if node.kind == "platform":
        return f"platform {node.platform}"
    return node.name or node.id


def describe_equipment(graph, equipment_id):
    """"the lift between the concourse and platform 2", or its recorded name."""
    item = graph.equipment.get(equipment_id)
    if item is None:
        return equipment_id
    if item.name:
        return item.name
    edges = graph.edges_of(item.id)
    if not edges:
        return f"the {item.kind} {item.id}"
    edge = graph.edges[edges[0]]
    return f"the {item.kind} between {describe(graph, edge.start)} and {describe(graph, edge.end)}"


MODE_WORDS = {
    "walkway": "a level walk", "ramp": "a ramp", "stairs": "stairs",
    "footbridge-stairs": "the footbridge stairs", "subway-stairs": "the subway stairs",
    "lift": "a lift", "escalator": "an escalator", "gate": "a gate",
    "unsurveyed": "a way nobody has recorded",
}


def describe_route(graph, edge_ids):
    """"a level walk to the concourse, then a lift to platform 2"."""
    if not edge_ids:
        return "level from the entrance"
    parts = []
    for i, edge_id in enumerate(edge_ids):
        edge = graph.edges[edge_id]
        what = MODE_WORDS[edge.mode]
        if edge.mode == "gate" and edge.gate:
            what = f"a {edge.gate.replace('-', ' ')}"
        prefix = "then " if i else ""
        parts.append(f"{prefix}{what} to {describe(graph, edge.end)}")
    return ", ".join(parts)


def _platforms(labels):
    labels = list(labels)
    if not labels:
        return "no platform"
    return f"platform{'s' if len(labels) > 1 else ''} {model._join(labels)}"


def _page_quotes(graph, edge_ids):
    quotes = []
    for edge_id in edge_ids:
        source = graph.edges[edge_id].source
        if source.get("kind") == "irishrail-page" and source.get("quote") not in quotes:
            quotes.append(source["quote"])
    return quotes


def _escalator(graph, joined, text):
    parts = [
        "An escalator is moving stairs, so it was not a step-free route to begin with "
        "and its being out did not remove one. Anyone who finds a flight of stairs "
        "hard, or has a buggy, a suitcase or a stick, did lose a way up."
    ]
    for item_id in joined:
        for edge_id in graph.edges_of(item_id):
            edge = graph.edges[edge_id]
            ends = {edge.start, edge.end}
            beside = sorted(
                other.equipment for other in graph.edges.values()
                if other.mode == "lift" and {other.start, other.end} == ends and other.equipment
            )
            between = f"between {describe(graph, edge.start)} and {describe(graph, edge.end)}"
            if beside:
                parts.append(
                    f"The survey records {'a lift' if len(beside) == 1 else 'lifts'} {between} "
                    "as well; the feed says nothing about whether that lift ran."
                )
            else:
                parts.append(f"The survey records no lift {between}, only the escalator.")
    return model.Verdict("escalator", (), " ".join(parts))


def verdict(graph, kind, text):
    """What a notice means at a surveyed station, in the four fields `model.Verdict` has."""
    leg = model.leg_named(text)
    named = model.affected_platforms(text)
    if not graph:
        return model.Verdict("unknown", named, "No survey of this station has been recorded.", leg)
    joined, unmatched = join_notice(graph, kind, text)
    if not joined:
        have = sorted(e.id for e in graph.equipment.values() if e.kind == kind)
        detail = (
            f"The survey records no {kind} matching this notice"
            + (f" ({kind}s recorded: {', '.join(have)})" if have else f" and no {kind} at all")
            + ", so what it served is not established."
        )
        return model.Verdict("unknown", named, detail, leg)
    if kind == "escalator":
        return _escalator(graph, joined, text)._replace(leg=leg)

    result = outcome(graph, kind, text)
    kept = routes(graph, frozenset(result.removed))
    parts = []
    which = model._join([describe_equipment(graph, item) for item in joined])
    if result.lost:
        subject = _platforms(result.lost)
        verb = "is" if len(result.lost) == 1 else "are"
        it = "it" if len(result.lost) == 1 else "them"
        parts.append(
            f"{subject[0].upper()}{subject[1:]} {verb} reached by {which} and the "
            f"survey records no other step-free way to {it}, so step-free access was gone "
            "while this was listed."
        )
    for label in result.unconfirmed:
        route = describe_route(graph, kept[graph.platforms()[label]])
        parts.append(
            f"The survey names a way round the lift to platform {label} ({route}) that "
            "nobody has confirmed, so it is not counted and platform "
            f"{label} is read as lost too."
        )
    for label in result.alternative:
        route = describe_route(graph, kept[graph.platforms()[label]])
        parts.append(f"Platform {label} kept a step-free way: {route}.")
    if result.unaffected:
        subject = _platforms(result.unaffected)
        parts.append(f"{subject[0].upper()}{subject[1:]} never needed this lift.")
    if result.never:
        subject = _platforms(result.never)
        parts.append(
            f"{subject[0].upper()}{subject[1:]} "
            + ("has" if len(result.never) == 1 else "have")
            + " no step-free route on the survey"
            + ("" if graph.complete else ", which is incomplete")
            + "."
        )
    if result.unmatched:
        parts.append(
            f"The notice also names {_platforms(result.unmatched)}, which no recorded "
            f"{kind} touches."
        )
    quoted_edges = list(result.removed)
    for label in result.unconfirmed:
        quoted_edges.extend(kept[graph.platforms()[label]])
    quotes = _page_quotes(graph, quoted_edges)
    if quotes:
        parts.append("Irish Rail's page: " + model._quoted(quotes) + ".")
    lost = tuple(result.lost) + tuple(result.unconfirmed)
    if lost:
        state = "lost"
    elif result.alternative:
        state = "alternative"
    else:
        state = "unknown"
        parts.insert(0, f"{which[0].upper()}{which[1:]} is on no step-free route to a "
                        "platform in the survey, so what its outage removed is not established.")
    return model.Verdict(state, lost or tuple(result.alternative), " ".join(parts), leg)


def contradictions(graph, station=None):
    """Things the log says that cannot all be true, or that the page has stopped saying."""
    out = []
    used = {e.equipment for e in graph.edges.values() if e.equipment}
    for item in graph.equipment.values():
        if item.id not in used:
            out.append(f"{item.kind} {item.id} is recorded but no edge belongs to it")
    entrances = set(graph.entrances())
    platform_nodes = set(graph.platforms().values())
    for item in graph.equipment.values():
        legs = set()
        for edge_id in graph.edges_of(item.id):
            edge = graph.edges[edge_id]
            ends = {edge.start, edge.end}
            if ends & entrances:
                legs.add("the way in")
            if ends & platform_nodes:
                legs.add("the platforms")
        if len(legs) > 1:
            out.append(f"{item.kind} {item.id} is on both {' and '.join(sorted(legs))}")
    labels = [n.platform for n in graph.nodes.values() if n.kind == "platform"]
    for label in sorted(set(labels)):
        if labels.count(label) > 1:
            out.append(f"platform {label} is recorded as more than one node")
    if station is not None:
        page = tuple(sorted(model.step_free_platforms(station)))
        reached = step_free_platforms(graph)
        for label, _ in page:
            if label in graph.platforms() and label not in reached:
                out.append(
                    f"Irish Rail's page calls platform {label} level but the survey "
                    "has no step-free route to it"
                )
    return out
