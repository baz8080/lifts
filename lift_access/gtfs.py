"""The graph as GTFS stops, pathways and levels, so anyone else can read it.

GTFS-Pathways is the graph this whole question needs and the one Ireland does
not publish (`notes/station-access.md` § Why scraping prose is the only
option). Exporting the survey in that shape means the NTA, Google, Apple or
Transit could take it as it stands. Provenance stays in the log: pathways.txt
has no column for who said so.

A walkway, ramp or plain gate recorded as not passable in a wheelchair has no
pathway_mode of its own, so it exports as stairs (mode 2), which every
consumer reads as not accessible; exported as a walkway it would be routed
through. A lift, escalator or ticket barrier keeps its own mode whatever the
flag says, since those modes carry meaning a consumer needs. Platform stops
carry `wheelchair_boarding` under the same gate as the verdict: 1 only where a
route somebody confirmed reaches the platform, 0 where only the page vouches
for one or the graph is incomplete, 2 where a complete graph reaches it by
nothing step-free. `unsurveyed` edges are not exported; they are the absence
of a record, and GTFS has no way to say that.
"""

from __future__ import annotations

import csv
from pathlib import Path

from . import graph as g

PATHWAY_MODE = {
    "walkway": 1, "ramp": 1, "stairs": 2, "footbridge-stairs": 2, "subway-stairs": 2,
    "escalator": 4, "lift": 5, "gate": 1,
}
GATE_MODE = {"ticket-barrier": 6}
LOCATION_TYPE = {"platform": 0, "entrance": 2, "concourse": 3, "landing": 3, "generic": 3}

STOP_COLUMNS = ("stop_id", "stop_name", "location_type", "parent_station", "platform_code",
                "wheelchair_boarding", "level_id", "stop_lat", "stop_lon")
PATHWAY_COLUMNS = ("pathway_id", "from_stop_id", "to_stop_id", "pathway_mode", "is_bidirectional",
                   "stair_count", "max_slope", "min_width")
LEVEL_COLUMNS = ("level_id", "level_index", "level_name")


def stop_id(graph, node=None):
    return graph.code if node is None else f"{graph.code}:{node}"


def stop_rows(graph, station=None):
    lat = (station.latitude if station else None) or ""
    lon = (station.longitude if station else None) or ""
    name = station.name if station else graph.code
    rows = [{
        "stop_id": stop_id(graph), "stop_name": name, "location_type": 1, "parent_station": "",
        "platform_code": "", "wheelchair_boarding": "", "level_id": "", "stop_lat": lat,
        "stop_lon": lon,
    }]
    # The same gate as the verdict: 1 only on a route somebody confirmed, 0
    # where only the page vouches for it or the graph is incomplete, 2 where a
    # complete graph reaches it by nothing step-free.
    confirmed = frozenset(g.routes(graph, confirmed_only=True))
    reached = g.reachable(graph)
    for node in graph.nodes.values():
        boarding = ""
        if node.kind == "entrance":
            boarding = 1
        elif node.kind == "platform":
            if node.id in confirmed:
                boarding = 1
            elif node.id in reached or not graph.complete:
                boarding = 0
            else:
                boarding = 2
        rows.append({
            "stop_id": stop_id(graph, node.id),
            "stop_name": node.name or (f"Platform {node.platform}" if node.platform else node.id),
            "location_type": LOCATION_TYPE[node.kind],
            "parent_station": stop_id(graph),
            "platform_code": node.platform or "",
            "wheelchair_boarding": boarding,
            "level_id": f"{graph.code}:{node.level}" if node.level else "",
            "stop_lat": lat if node.kind == "entrance" else "",
            "stop_lon": lon if node.kind == "entrance" else "",
        })
    return rows


def pathway_rows(graph):
    rows = []
    for edge in graph.edges.values():
        if edge.mode == "unsurveyed":
            continue
        if edge.mode == "gate":
            mode = GATE_MODE.get(edge.gate, PATHWAY_MODE["gate"])
        else:
            mode = PATHWAY_MODE[edge.mode]
        if edge.wheelchair is False and mode == PATHWAY_MODE["walkway"]:
            mode = PATHWAY_MODE["stairs"]
        rows.append({
            "pathway_id": f"{graph.code}:{edge.id}",
            "from_stop_id": stop_id(graph, edge.start),
            "to_stop_id": stop_id(graph, edge.end),
            "pathway_mode": mode,
            "is_bidirectional": 1 if edge.bidirectional else 0,
            "stair_count": edge.stair_count if edge.stair_count is not None else "",
            "max_slope": edge.slope if edge.slope is not None else "",
            "min_width": edge.width if edge.width is not None else "",
        })
    return rows


def level_rows(graph):
    return [
        {"level_id": f"{graph.code}:{level.id}", "level_index": level.index,
         "level_name": level.name or ""}
        for level in graph.levels.values()
    ]


def _write(path, columns, rows):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def export(graphs, facts, out_dir):
    """Write stops.txt, pathways.txt and, when any level is recorded, levels.txt."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stops, pathways, levels = [], [], []
    for graph in graphs:
        station = facts.station(graph.code) if facts else None
        stops.extend(stop_rows(graph, station))
        pathways.extend(pathway_rows(graph))
        levels.extend(level_rows(graph))
    _write(out_dir / "stops.txt", STOP_COLUMNS, stops)
    _write(out_dir / "pathways.txt", PATHWAY_COLUMNS, pathways)
    written = [out_dir / "stops.txt", out_dir / "pathways.txt"]
    if levels:
        _write(out_dir / "levels.txt", LEVEL_COLUMNS, levels)
        written.append(out_dir / "levels.txt")
    return written
