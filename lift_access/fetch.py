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

from . import model

SITE = "https://www.irishrail.ie"

# Every station payload carries the full station list, but the find-a-station
# page is the one whose job that is, so a slug going away cannot strand us.
INDEX_URL = f"{SITE}/en-ie/travel-information/find-a-station/_payload.json"

USER_AGENT = "lifts-status/1.0 (+https://github.com/baz8080/lifts)"

# Keyed under this in `failed` when the station list itself could not be read, so
# the caller can say "the run never started" rather than counting it as a station.
INDEX_FAILED = "(station index)"

# Polite serial fetching. The whole run is ~150 requests and takes about three
# minutes; there is no deadline on a monthly job.
DELAY_SECONDS = 0.3

# A 5xx or a dropped connection on one station is usually transient. Widens per
# attempt, because the alternative is failing a monthly job over one blip.
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


def _yields_station(slug, body):
    """Does this payload actually carry a station, or only look like one?

    A 200 with a non-empty body proves the transport worked, not that the CMS
    still shapes its payload the way `station_node` reads it. A renamed cache
    key writes a snapshot of clean records that read back as no stations at all,
    and the site publishes whatever survived as the national denominator.
    """
    try:
        node = station_node(json.loads(body))
    except json.JSONDecodeError:
        return False
    return model.station_from_node(node, slug) is not None


def fetch_stations(log=print, attempts=3):
    """Every station payload, verbatim, and the slugs it could not get.

    Returns both. The caller must not write a partial snapshot: a station missing
    from it is not a station without facts, it is a station whose published
    verdict silently becomes "unknown" and which drops out of the denominator,
    and the newest file on disk is the one the site reads. Transient failures are
    retried before a slug is given up on.

    A station counts as fetched only if its payload reads back as one, because
    the snapshot is written verbatim and nothing downstream refuses it.
    """
    try:
        _, index_body = _get(INDEX_URL)
        slugs = station_slugs(json.loads(index_body))
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        # Without the index there is no list to fetch, and an HTML error page
        # where the payload should be is a JSONDecodeError, not an OSError.
        return [], {INDEX_FAILED: f"{type(exc).__name__}: {exc}"}
    log(f"{len(slugs)} stations listed")
    records, failed = [], {}
    for n, slug in enumerate(slugs, 1):
        url = f"{SITE}/en-ie/station/{slug}/_payload.json"
        for attempt in range(attempts):
            try:
                status, body = _get(url)
                if status != 200 or not body:
                    failed[slug] = f"HTTP {status}, {len(body)} bytes"
                elif not _yields_station(slug, body):
                    failed[slug] = f"HTTP {status}, {len(body)} bytes, but no station in it"
                else:
                    records.append({"slug": slug, "http_status": status, "body": body})
                    failed.pop(slug, None)
                    break
            except urllib.error.HTTPError as exc:
                failed[slug] = f"HTTP {exc.code}"
            except Exception as exc:  # noqa: BLE001 - reported, never swallowed
                # Broad on purpose. A body that is not UTF-8 raises
                # UnicodeDecodeError, which is neither HTTPError nor OSError, and
                # would abort a run whose whole job is to say which stations it
                # could not get.
                failed[slug] = f"{type(exc).__name__}: {exc}"
            if attempt < attempts - 1:
                time.sleep(BACKOFF_SECONDS * (attempt + 1))
        if n % 25 == 0:
            log(f"  {n}/{len(slugs)}")
        time.sleep(DELAY_SECONDS)
    return records, failed


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
