"""CLI entry point: python -m lift_access

`refresh` fetches the station facts and writes the snapshot they are derived
from. `report` prints what the current snapshot says, station by station, beside
the prose it came from - which is the only real check on a derivation built out
of somebody's hand-written sentences. Read it before publishing.

Neither runs on the Pi, and neither belongs in the 30-minute poll loop.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

from lift_status.store import DB_FILENAME, DEFAULT_DATA_DIR

from . import fetch, model, snapshot

SNAPSHOT_DIR = snapshot.SNAPSHOT_DIR
STATIONS_PREFIX = snapshot.STATIONS_PREFIX
OSM_PREFIX = snapshot.OSM_PREFIX


def refresh(args):
    directory = Path(args.data_dir) / SNAPSHOT_DIR
    stamp = datetime.now(UTC).strftime("%Y%m%d")

    records = fetch.fetch_stations()
    failed = [r["slug"] for r in records if r["http_status"] != 200]
    if failed:
        print(f"warning: {len(failed)} station(s) did not return 200: {', '.join(failed[:5])}",
              file=sys.stderr)
    path = fetch.write_snapshot(directory / f"{STATIONS_PREFIX}-{stamp}.jsonl", records)
    print(f"wrote {path} ({len(records)} stations)")

    stations = []
    for record in records:
        if not record["body"]:
            continue
        node = fetch.station_node(json.loads(record["body"]))
        station = model.station_from_node(node, record["slug"])
        if station:
            stations.append(station)

    if args.skip_osm:
        print("skipped the OSM cross-check")
        return 0
    print("cross-checking against OpenStreetMap")
    digests, failed = fetch.fetch_osm(stations)
    if failed:
        # Refused, not warned. The cross-check only ever suppresses a claim, so
        # a station missing from it makes the site more confident about that
        # station, not less - which is the one direction of error this whole
        # module exists to avoid. The station snapshot above is already written
        # and is the useful half; rerun for the OSM half.
        for code, why in sorted(failed.items())[:10]:
            print(f"  {code}: {why}", file=sys.stderr)
        print(
            f"error: OpenStreetMap returned nothing for {len(failed)} of {len(stations)} "
            "stations, so no digest was written. OSM rate-limits a long burst; rerun "
            "in a few minutes.",
            file=sys.stderr,
        )
        return 1
    path = fetch.write_snapshot(directory / f"{OSM_PREFIX}-{stamp}.jsonl", digests)
    print(f"wrote {path} ({len(digests)} stations)")
    return 0


def _notices(db_path):
    """(code, kind, text) for every lift and escalator notice on record."""
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
            out.append((listed[0], kind, head, text))
    return out


def report(args):
    facts = snapshot.load(args.data_dir)
    if not facts:
        print(f"no station snapshot under {Path(args.data_dir) / SNAPSHOT_DIR}\n"
              f"run: python -m lift_access --data-dir {args.data_dir} refresh", file=sys.stderr)
        return 1
    stations, digests, path = facts.stations, facts.osm, facts.path
    print(f"{len(stations)} stations from {path}\n")

    tally = facts.tally()
    print(f"lift: {tally['yes']} yes, {tally['no']} no, {tally['unknown']} unknown\n")

    db_path = Path(args.data_dir) / DB_FILENAME
    if db_path.exists():
        print("--- what each notice on record means ---")
        for code, kind, head, text in _notices(db_path):
            station = stations.get(code)
            result = model.verdict(station, kind, text, digests.get(code))
            print(f"\n  {code:6} {head}")
            print(f"    prose:   {(station.platform_access if station else '(no station)')[:150]}")
            print(f"    notice:  {model.plain(text)[:150]}")
            print(f"    -> {result.state.upper()}: {result.detail}")

    if args.all:
        print("\n--- every station that claims a lift ---")
        for code in sorted(stations):
            station = stations[code]
            if not station.claims_lift:
                continue
            serves = "all" if model.ALL_PLATFORMS in station.lift_platforms else (
                ", ".join(sorted(station.lift_platforms)) or "none named")
            print(f"\n  {code:6} {station.name}  (lift at: {serves})")
            print(f"    {station.platform_access[:200]}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="lift_access", description="Station accessibility facts for the lift site."
    )
    parser.add_argument("--data-dir", default=DEFAULT_DATA_DIR,
                        help="collector storage root (env: LIFT_STATUS_DATA_DIR)")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch_cmd = sub.add_parser("refresh", help="fetch the station facts and write the snapshot")
    fetch_cmd.add_argument("--skip-osm", action="store_true",
                           help="station payloads only, no OpenStreetMap cross-check")
    fetch_cmd.set_defaults(run=refresh)

    report_cmd = sub.add_parser("report", help="print what the current snapshot says")
    report_cmd.add_argument("--all", action="store_true",
                            help="also print every station that claims a lift")
    report_cmd.set_defaults(run=report)

    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
