"""Fetching the station facts, and writing the snapshot they are derived from.

Irish Rail's station pages are a Nuxt app, and every one of them serves its data
as JSON at `<page>/_payload.json`. That is the source here: named fields, no HTML
parsing, and one of the fields is `stationCode`, which is the same code space the
message feed's `locationCodes` uses. `robots.txt` disallows only `/stations.csv`.

Nothing here runs on the Pi or in the 30-minute poll loop - it is ~150 requests
against a CMS that changes a few times a year. See `notes/station-access.md`.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime

SITE = "https://www.irishrail.ie"

# Every station payload carries the full station list, but the find-a-station
# page is the one whose job that is, so a slug going away cannot strand us.
INDEX_URL = f"{SITE}/en-ie/travel-information/find-a-station/_payload.json"

# OSM's own map API rather than Overpass: Overpass was rate-limiting and
# 500ing across three endpoints while this was written, and the map API served
# all 152 bboxes without a single failure.
OSM_URL = "https://api.openstreetmap.org/api/0.6/map.json"

# ~250 m either side of the station point. Wide enough for a long platform,
# narrow enough not to drag in the shopping centre next door.
OSM_HALF_SPAN = 0.0028

OSM_ATTRIBUTION = "http://www.openstreetmap.org/copyright"

USER_AGENT = "lifts-status/1.0 (+https://github.com/baz8080/lifts)"

# Polite serial fetching. The whole run is ~150 requests and takes about three
# minutes; there is no deadline on a monthly job.
DELAY_SECONDS = 0.3

# OSM answers a long burst with 429 and 509. Widens per attempt.
BACKOFF_SECONDS = 5


def _get(url, timeout=60):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8")


def _now():
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve(payload, index=0, _depth=0):
    """One node of a Nuxt payload, with its references followed.

    The payload is a flat list in which every dict value and list element is an
    integer pointing at another slot. `_depth` is a cycle guard: the graph is
    not a tree, and the menus in particular refer back to themselves.
    """
    if _depth > 12 or not isinstance(index, int) or not 0 <= index < len(payload):
        return None
    node = payload[index]
    if isinstance(node, dict):
        return {k: resolve(payload, v, _depth + 1) for k, v in node.items()}
    if isinstance(node, list):
        return [resolve(payload, v, _depth + 1) for v in node]
    return node


def _root(payload):
    """The `{cache-key: slot}` map every payload puts in slot 2."""
    return payload[2] if len(payload) > 2 and isinstance(payload[2], dict) else {}


def station_node(payload):
    """The station object out of one station page's payload, or None."""
    for key, slot in _root(payload).items():
        if key.startswith("station-station/"):
            return resolve(payload, slot)
    return None


def station_slugs(payload):
    """Every station's slug, from the find-a-station payload's `kontentStations`."""
    for key, slot in _root(payload).items():
        if key.startswith("kontentStations"):
            listed = resolve(payload, slot) or []
            return sorted(
                s["slug"].rsplit("/", 1)[-1]
                for s in listed
                if isinstance(s, dict) and s.get("slug")
            )
    return []


def fetch_stations(log=print):
    """Every station payload, verbatim, as `{slug, http_status, body}` records.

    The body is kept as the text that came back rather than as parsed JSON: it is
    the artefact, and the snapshot has to be re-derivable when the parse changes.
    """
    _, index_body = _get(INDEX_URL)
    slugs = station_slugs(json.loads(index_body))
    log(f"{len(slugs)} stations listed")
    records = []
    for n, slug in enumerate(slugs, 1):
        url = f"{SITE}/en-ie/station/{slug}/_payload.json"
        try:
            status, body = _get(url)
        except urllib.error.HTTPError as exc:
            status, body = exc.code, ""
        except OSError as exc:
            log(f"  {slug}: {exc}")
            status, body = 0, ""
        records.append({"slug": slug, "http_status": status, "body": body})
        if n % 25 == 0:
            log(f"  {n}/{len(slugs)}")
        time.sleep(DELAY_SECONDS)
    return records


def osm_digest(code, lat, lon):
    """What OSM has mapped inside one station's box.

    A count, not the response. The full map extracts total ~450 MB across the
    network - Pearse's box alone is 3 MB - which cannot go in a git repository,
    so this is the one derived artefact in the snapshot rather than a verbatim
    one. It is only ever used to *contradict* Irish Rail's prose, never to make
    a claim of its own, which is what makes the compromise tolerable.
    """
    box = (lon - OSM_HALF_SPAN, lat - OSM_HALF_SPAN, lon + OSM_HALF_SPAN, lat + OSM_HALF_SPAN)
    url = f"{OSM_URL}?bbox={box[0]:.4f},{box[1]:.4f},{box[2]:.4f},{box[3]:.4f}"
    status, body = _get(url)
    data = json.loads(body)
    lifts = escalators = platforms = 0
    for element in data.get("elements", []):
        tags = element.get("tags") or {}
        if tags.get("highway") == "elevator":
            lifts += 1
        elif tags.get("highway") == "steps" and tags.get("conveying"):
            escalators += 1
        if tags.get("railway") == "platform":
            platforms += 1
    # ODbL requires attribution wherever this is redistributed, and the snapshot
    # is committed to a public repository, so it travels with the data.
    return {
        "code": code,
        "bbox": [round(v, 4) for v in box],
        "source": data.get("attribution") or OSM_ATTRIBUTION,
        "lifts": lifts,
        "escalators": escalators,
        "platforms": platforms,
    }


def fetch_osm(stations, log=print, attempts=4):
    """An OSM digest per station, and the stations it could not get.

    Returns both, and the caller must not write a partial digest: OSM only ever
    *suppresses* a claim here, so a station missing from it silently makes the
    site more confident rather than less. A truncated cross-check is worse than
    none, because it looks like one.

    OSM answers a burst of 150 boxes with 429s and 509s, so each station is
    retried with a widening wait before it is given up on.
    """
    digests, failed = [], {}
    for n, station in enumerate(stations, 1):
        try:
            lat, lon = float(station.latitude), float(station.longitude)
        except (TypeError, ValueError):
            failed[station.code] = "no coordinates in the station payload"
            continue
        for attempt in range(attempts):
            try:
                digests.append(osm_digest(station.code, lat, lon))
                failed.pop(station.code, None)
                break
            except Exception as exc:  # noqa: BLE001 - reported, never swallowed
                failed[station.code] = f"{type(exc).__name__}: {exc}"
                if attempt < attempts - 1:
                    time.sleep(BACKOFF_SECONDS * (attempt + 1))
        if n % 25 == 0:
            log(f"  {n}/{len(stations)}")
        time.sleep(DELAY_SECONDS)
    return digests, failed


def write_snapshot(path, records, fetched_at=None):
    """One JSONL file, sorted, `sort_keys=True`, in the shape `store.write_raw` uses.

    Sorted so that two refreshes of unchanged data produce an identical file and
    the scheduled job opens no PR.
    """
    fetched_at = fetched_at or _now()
    lines = sorted(
        json.dumps({"fetched_at_utc": fetched_at, **record}, sort_keys=True) for record in records
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def latest_snapshot(directory, prefix):
    """The newest `<prefix>-<date>.jsonl` in `directory`, or None."""
    found = sorted(directory.glob(f"{prefix}-*.jsonl")) if directory.is_dir() else []
    return found[-1] if found else None


def load_records(path):
    """Every record in a snapshot, skipping any line a truncated write left behind."""
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records
