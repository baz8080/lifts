"""Reading the station snapshot back, for the site build and for `report`.

Both callers want the same thing and neither should have to know that a payload
is a Nuxt reference graph. A missing snapshot is not an error: the site built
without one for months and still does, it just cannot say anything about what a
station has.
"""

from __future__ import annotations

import json
from pathlib import Path

from . import fetch, model

SNAPSHOT_DIR = "stations"
STATIONS_PREFIX = "irishrail"


class Facts:
    """What the newest snapshot says, or an empty one when there is none."""

    def __init__(self, stations=None, path=None):
        self.stations = stations or {}
        self.path = path

    def __bool__(self):
        return bool(self.stations)

    def station(self, code):
        return self.stations.get(code)

    def has_lift(self, code):
        """'yes' or 'no' for a station in the snapshot, 'unknown' for one that is not."""
        station = self.stations.get(code)
        return model.has_lift(station) if station else "unknown"

    def verdict(self, code, kind, text):
        return model.verdict(self.stations.get(code), kind, text)

    def tally(self):
        """How many stations have a lift, of those in the snapshot."""
        counts = {"yes": 0, "no": 0}
        for code in self.stations:
            counts[self.has_lift(code)] += 1
        return counts


def load(data_dir):
    directory = Path(data_dir) / SNAPSHOT_DIR
    stations_path = fetch.latest_snapshot(directory, STATIONS_PREFIX)
    if stations_path is None:
        return Facts()
    stations = {}
    for record in fetch.load_records(stations_path):
        if not record.get("body"):
            continue
        try:
            node = fetch.station_node(json.loads(record["body"]))
        except json.JSONDecodeError:
            continue
        station = model.station_from_node(node, record.get("slug", ""))
        if station:
            stations[station.code] = station
    return Facts(stations, stations_path)
