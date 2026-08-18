"""CLI entry point: python -m lift_status <command>"""

from __future__ import annotations

import argparse
import os
import sys

from . import __version__, alert
from .client import MessagesClient
from .poll import run_check, run_poll, run_rebuild
from .store import Store

DEFAULT_DATA_DIR = os.environ.get("LIFT_STATUS_DATA_DIR", "/data")


def _human_bytes(n: int) -> str:
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024 or unit == "GiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n:.1f} GiB"


def cmd_stats(args) -> int:
    with Store(args.data_dir) as store:
        s = store.stats()
    print(f"messages tracked : {s['messages_total']}")
    print(f"  currently open  : {s['open']}")
    print(f"  closed          : {s['closed']}")
    print(f"  reopened at least once : {s['reopened']}")
    print(f"unidentifiable items    : {s['unidentifiable']}")
    print(f"runs recorded    : {s['runs']}")
    print(f"coverage         : {s['first_run'] or '-'} .. {s['last_run'] or '-'}")
    print(f"raw log size     : {_human_bytes(s['raw_bytes'])}")
    print(f"database size    : {_human_bytes(s['db_bytes'])}")
    if s["by_outcome"]:
        print("\nrun outcomes:")
        for outcome, n in s["by_outcome"]:
            print(f"    {outcome:<12} {n}")
    if s["recent_runs"]:
        print("\nrecent runs:")
        print(f"  {'started':<21}{'outcome':<13}{'items':>7}{'drift':>7}")
        for r in s["recent_runs"]:
            print(
                f"  {r['started_at_utc']:<21}{r['outcome']:<13}"
                f"{r['item_count'] if r['item_count'] is not None else '-':>7}"
                f"{r['schema_drift_count']:>7}"
            )
    return alert.EXIT_OK


def cmd_test_alert(args) -> int:
    """Fire a real alert through the real channel.

    Exists because an untested alarm is not an alarm, and the alternative way
    to test it - deliberately breaking the API key - stops collection while
    you do.
    """
    if not os.environ.get("LIFT_STATUS_ALERT_WEBHOOK"):
        print(
            "LIFT_STATUS_ALERT_WEBHOOK is not set, so failures would reach nobody.\n"
            "Set it in /etc/lift-status.env, e.g. an ntfy.sh topic URL.",
            file=sys.stderr,
        )
        return 1
    message = alert.banner(
        "LIFT-STATUS: TEST ALERT",
        [
            "This is a test. Nothing is wrong.",
            "",
            "If you are reading this, a real failure would have reached you too.",
        ],
    )
    print(message)
    if not alert.notify(message, dedup=False):
        print("alert delivery FAILED - see the warning above", file=sys.stderr)
        return 1
    print("alert delivered")
    return alert.EXIT_OK


def cmd_rebuild(args) -> int:
    return run_rebuild(args.data_dir)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="lift_status", description="Collect Irish Rail lift-status messages."
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--data-dir", default=DEFAULT_DATA_DIR, help="storage root (env: LIFT_STATUS_DATA_DIR)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("poll", help="run one collection pass (the scheduled command)")
    sub.add_parser("check", help="verify the API key and connectivity; writes nothing")
    sub.add_parser("test-alert", help="send a test alert through LIFT_STATUS_ALERT_WEBHOOK")
    sub.add_parser("rebuild", help="rebuild the database from the raw JSONL logs")
    sub.add_parser("stats", help="summarise what has been collected")

    args = parser.parse_args(argv)

    if args.command == "poll":
        return run_poll(args.data_dir)
    if args.command == "check":
        return run_check(MessagesClient())
    if args.command == "test-alert":
        return cmd_test_alert(args)
    if args.command == "rebuild":
        return cmd_rebuild(args)
    if args.command == "stats":
        return cmd_stats(args)
    return alert.EXIT_OK  # pragma: no cover - argparse enforces a command


if __name__ == "__main__":
    sys.exit(main())
