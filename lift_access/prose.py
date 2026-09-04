"""A station's graph as the page Irish Rail could publish, written for a passenger.

The proposal to Irish Rail (`notes/step-free-graph.md` § A format to propose)
is a fixed order of questions answered in sentences, one per platform, with
the failure case in the same breath. Rendering the graph in that layout does
two jobs: the pilot stations become worked examples, and a fact the layout
cannot say is a test failure rather than a silent omission. The confidence
gate applies here as it does to the verdict: a route with a page-only edge on
it is "yes, according to Irish Rail's page, which nobody has confirmed".
"""

from __future__ import annotations

from . import graph as g

WORDS = {
    "walkway": "level", "ramp": "a ramp", "stairs": "stairs",
    "footbridge-stairs": "the footbridge stairs", "subway-stairs": "the subway stairs",
    "lift": "a lift", "escalator": "an escalator", "gate": "a gate",
    "unsurveyed": "not yet recorded",
}


def _cap(text):
    return text[0].upper() + text[1:] if text else text


def _lift_ids(graph, route):
    return sorted({graph.edges[e].equipment for e in route if graph.edges[e].mode == "lift"})


def _unconfirmed(graph, route):
    return any(graph.edges[e].confidence not in g.CONFIRMED for e in route)


UNCONFIRMED = "according to Irish Rail's page, which nobody has confirmed"


def _ways(graph, node, stepped_only):
    ways = []
    for edge in graph.edges.values():
        if node not in (edge.start, edge.end) or edge.mode == "unsurveyed":
            continue
        if stepped_only and g.step_free(edge):
            continue
        other = edge.start if edge.end == node else edge.end
        ways.append(f"{WORDS[edge.mode]} from {g.describe(graph, other)}")
    return ways


def _platform_paragraph(graph, label, node, route):
    node_name = graph.nodes[node].name
    heading = f"Platform {label}" + (f", {node_name}" if node_name else "")
    if route is None:
        if graph.complete:
            ways = _ways(graph, node, stepped_only=True)
            body = "no. " + (f"It is reached by {', or '.join(ways)}." if ways
                             else "The survey records no way to it without steps.")
        else:
            ways = _ways(graph, node, stepped_only=False)
            body = "not yet known, because the survey of this station is incomplete." + (
                f" Recorded so far: {', and '.join(ways)}." if ways else "")
        return f"{heading}: {body}\n"
    lifts = _lift_ids(graph, route)
    yes = "yes, by lift" if lifts else "yes"
    if _unconfirmed(graph, route):
        yes += f", {UNCONFIRMED}"
    text = f"{heading}: {yes}. {_cap(g.describe_route(graph, route))}."
    if not lifts:
        return text + "\n"
    removed = frozenset(e for lift in lifts for e in graph.edges_of(lift))
    without = g.routes(graph, removed).get(node)
    if without is None:
        text += (f" If the lift is out of service there is no step-free way to "
                 f"platform {label}.")
    elif _unconfirmed(graph, without):
        text += (f" If the lift is out of service the page names a way round "
                 f"({g.describe_route(graph, without)}) that nobody has confirmed.")
    else:
        text += f" If the lift is out of service: {g.describe_route(graph, without)}."
    return text + "\n"


def render(graph, station=None):
    name = station.name if station is not None else graph.code
    out = [f"{name}\n\n", "Getting to the platforms without steps\n\n"]
    reached = g.routes(graph)
    platforms = graph.platforms()
    if not platforms:
        out.append("No platform has been recorded for this station yet.\n")
    for label, node in platforms.items():
        out.append(_platform_paragraph(graph, label, node, reached.get(node)))
        out.append("\n")

    out.append("Getting into the station\n\n")
    entrances = graph.entrances()
    if not entrances:
        out.append("No entrance has been recorded for this station yet.\n\n")
    for entrance in entrances:
        edges = [e for e in graph.edges.values() if entrance in (e.start, e.end)]
        who = _cap(g.describe(graph, entrance))
        if not edges:
            out.append(f"{who}: nothing recorded beyond the door.\n")
            continue
        ways = []
        for edge in sorted(edges, key=lambda e: (e.mode != "walkway", e.mode)):
            other = edge.start if edge.end == entrance else edge.end
            if edge.mode == "unsurveyed":
                ways.append(f"how you reach {g.describe(graph, other)} is {WORDS[edge.mode]}")
            else:
                ways.append(f"{WORDS[edge.mode]} to {g.describe(graph, other)}"
                            + (f" ({edge.hours})" if edge.hours else ""))
        out.append(f"{who}: {'; '.join(ways)}.\n")
    out.append("\n")

    out.append("Lifts and escalators here\n\n")
    for kind, plural in (("lift", "lifts"), ("escalator", "escalators")):
        items = [e for e in graph.equipment.values() if e.kind == kind]
        if not items:
            out.append(f"No {plural} recorded.\n")
            continue
        count = {1: "One", 2: "Two", 3: "Three", 4: "Four"}.get(len(items), str(len(items)))
        out.append(f"{count} {kind if len(items) == 1 else plural}.\n")
        for item in items:
            spans = []
            for edge_id in graph.edges_of(item.id):
                edge = graph.edges[edge_id]
                spans.append(f"between {g.describe(graph, edge.start)} and "
                             f"{g.describe(graph, edge.end)}")
            line = f"- {_cap(item.name) if item.name else _cap(kind) + ' ' + item.id}: " \
                   f"{'; '.join(spans) or 'no way recorded for it'}"
            if item.call:
                line += ", called from a help point"
            if item.hours:
                line += f", {item.hours}"
            out.append(line + ".\n")
    if graph.notes:
        out.append("\nStill to record\n\n")
        for text, _ in graph.notes:
            out.append(f"- {text}\n")
    return "".join(out)
