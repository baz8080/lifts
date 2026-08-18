"""CLI entry point: python -m lift_site"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from lift_status.store import DB_FILENAME, DEFAULT_DATA_DIR

from . import model, render

DEFAULT_OUT = "out/site"


def _parse_now(value):
    """An ISO timestamp from the command line, as UTC.

    Accepts the trailing `Z` the collector itself writes - `fromisoformat` only
    learned it in 3.11, and this has to run on the 3.9 floor - and converts an
    explicit offset rather than overwriting it.
    """
    text = value.strip()
    if text.endswith(("Z", "z")):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="lift_site", description="Build the static Irish Rail lift-outage status site."
    )
    parser.add_argument(
        "--data-dir",
        default=DEFAULT_DATA_DIR,
        help="collector storage root (env: LIFT_STATUS_DATA_DIR)",
    )
    parser.add_argument("--out", default=DEFAULT_OUT, help=f"output directory ({DEFAULT_OUT})")
    parser.add_argument(
        "--now",
        default=None,
        help="override the build clock, as an ISO UTC timestamp (for reproducible builds)",
    )
    args = parser.parse_args(argv)

    db_path = Path(args.data_dir) / DB_FILENAME
    if not db_path.exists():
        print(
            f"no database at {db_path}\n"
            f"run: python -m lift_status --data-dir {args.data_dir} rebuild",
            file=sys.stderr,
        )
        return 1

    now = _parse_now(args.now) if args.now else datetime.now(timezone.utc)

    outages, until = model.load_outages(db_path, now)
    if not outages:
        print("no lift or escalator notices in the database", file=sys.stderr)
        return 1

    data = render.write(args.out, outages, now, until)

    print(
        f"built {args.out} from {len(outages)} outages across "
        f"{len(data['stations'])} stations"
    )
    # The horizon, not the clock: everything measured stops here, and a gap
    # between the two is a collector that has stopped rather than a quiet week.
    lag = now - until
    print(f"  data covers up to {until:%Y-%m-%d %H:%M}Z ({lag.total_seconds() / 3600:.1f}h behind)")
    if data["stale"]:
        print(
            "  WARNING: the collected data is stale; days past the horizon "
            "are published as no-data",
            file=sys.stderr,
        )
    c = data["current"]
    print(
        f"  listed at the horizon: {c['lifts']} lift and {c['escalators']} escalator notice(s) "
        f"across {c['stations']} station(s)"
    )
    total, report = render.size_report(args.out)
    print(report)
    if total > render.BUDGET_BYTES:
        print(
            f"  WARNING: initial load is over the {render.BUDGET_BYTES // 1024} KB budget",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
