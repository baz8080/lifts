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


def refresh(args):
    directory = Path(args.data_dir) / SNAPSHOT_DIR
    stamp = datetime.now(UTC).strftime("%Y%m%d")

    records, failed = fetch.fetch_stations()
    if fetch.INDEX_FAILED in failed:
        # No station was attempted, so counting this as a failed station reads as
        # "1 of 1 stations could not be fetched", which is nonsense.
        print(
            f"error: could not read the station list from {fetch.INDEX_URL}\n"
            f"  {failed[fetch.INDEX_FAILED]}\n"
            "No stations were fetched and no snapshot was written.",
            file=sys.stderr,
        )
        return 1
    if failed:
        # Refused, not warned. `latest_snapshot` reads the newest file, so a
        # partial one shadows the last good snapshot permanently, and the damage
        # is invisible: those stations lose their verdicts and the denominator
        # quietly shrinks. An 8 MB JSONL diff will not show a reviewer 38 empty
        # bodies either.
        for slug, why in sorted(failed.items())[:10]:
            print(f"  {slug}: {why}", file=sys.stderr)
        print(
            f"error: {len(failed)} of {len(failed) + len(records)} stations could not be "
            "fetched, so no snapshot was written. The last good snapshot is untouched; "
            "rerun when irishrail.ie is healthy.",
            file=sys.stderr,
        )
        return 1
    if not records:
        # The guard above counts failures, and an index that parses but names no
        # station produces none: `station_slugs` keys off `kontentStations`, a CMS
        # internal that is nobody's promise. Renamed, every fetch is skipped, the
        # empty snapshot becomes the newest file, and the site loses every verdict
        # and its denominator without a single error.
        print(
            f"error: the station list at {fetch.INDEX_URL} parsed but named no stations, "
            "so nothing was fetched and no snapshot was written. The payload's shape has "
            "probably changed; check fetch.station_slugs against it.",
            file=sys.stderr,
        )
        return 1
    path = fetch.write_snapshot(directory / f"{STATIONS_PREFIX}-{stamp}.jsonl", records)
    print(f"wrote {path} ({len(records)} stations)")
    return 0


def _notices(db_path):
    """Every lift and escalator notice on record, for `report` to print.

    Four fields: the station's location code; "lift" or "escalator", which
    `classify` reads off the head; the head, which is the feed's own name for the
    hand-written headline ("Tullamore - Lift out of order"); and the notice body
    as the feed wrote it, which is the form `verdict` takes. `locationCodes[0]`
    is the whole station, every lift notice naming exactly one.
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
            out.append((listed[0], kind, head, text))
    return out


def report(args):
    """Every verdict beside the prose it was read from.

    Prints the entrance prose too where the verdict read it: an escalator notice
    or a lift notice that names the way in. It has no listings, so it never sets
    `lift_listed_too`; that is the site build's knowledge, not the snapshot's.
    """
    facts = snapshot.load(args.data_dir)
    if not facts:
        print(f"no station snapshot under {Path(args.data_dir) / SNAPSHOT_DIR}\n"
              f"run: python -m lift_access --data-dir {args.data_dir} refresh", file=sys.stderr)
        return 1
    stations, path = facts.stations, facts.path
    print(f"{len(stations)} stations from {path}\n")
    if facts.dropped:
        print(
            f"warning: {facts.dropped} record(s) in {path.name} read back as no station. "
            "refresh refuses to write one it cannot read, so the payload shape has moved "
            "under fetch.station_node since this file was written.",
            file=sys.stderr,
        )

    tally = facts.tally()
    print(f"lift: {tally['yes']} yes, {tally['no']} no\n")

    db_path = Path(args.data_dir) / DB_FILENAME
    if db_path.exists():
        print("--- what each notice on record means ---")
        for code, kind, head, text in _notices(db_path):
            station = stations.get(code)
            result = model.verdict(station, kind, text)
            print(f"\n  {code:6} {head}")
            print(f"    prose:   {(station.platform_access if station else '(no station)')[:150]}")
            if station and (kind == "escalator" or result.leg == model.ENTRANCE_LEG):
                entry = " / ".join(station.ticket_office_access.split("\n"))
                print(f"    entry:   {' '.join(entry.split())[:150]}")
                print(f"    leg:     {result.leg or 'not named'}")
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
    fetch_cmd.set_defaults(run=refresh)

    report_cmd = sub.add_parser("report", help="print what the current snapshot says")
    report_cmd.add_argument("--all", action="store_true",
                            help="also print every station that claims a lift")
    report_cmd.set_defaults(run=report)

    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    sys.exit(main())
