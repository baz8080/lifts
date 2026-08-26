"""Durable storage: append-only JSONL raw logs + a derived, disposable SQLite DB.

The JSONL log is the source of truth - it holds one line per poll *attempt*,
success or failure, written before any parsing happens. The SQLite database is
entirely derivable from it (see poll.run_rebuild) and can be deleted and
rebuilt at any time, including after a bug fix in parse.py changes how old
responses should have been interpreted.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from datetime import UTC, datetime
from pathlib import Path

DB_FILENAME = "lift_status.db"
RAW_DIRNAME = "raw"

# Both entry points read this. One name, so `lift_status rebuild` and
# `lift_site` with no flags can never look in two different places.
DEFAULT_DATA_DIR = os.environ.get("LIFT_STATUS_DATA_DIR", "/data")

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_uuid TEXT UNIQUE NOT NULL,
    started_at_utc TEXT NOT NULL,
    finished_at_utc TEXT NOT NULL,
    outcome TEXT NOT NULL,
    http_status INTEGER,
    item_count INTEGER,
    schema_drift_count INTEGER NOT NULL DEFAULT 0,
    error_detail TEXT,
    exit_code INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    identity_key TEXT UNIQUE NOT NULL,
    head TEXT NOT NULL,
    text_raw TEXT,
    start_raw TEXT NOT NULL,
    start_utc TEXT,
    end_raw TEXT,
    end_utc TEXT,
    location_codes TEXT NOT NULL,
    products TEXT,
    event_stops TEXT,
    tz_ambiguous INTEGER NOT NULL DEFAULT 0,
    first_seen_run_id INTEGER NOT NULL,
    first_seen_at_utc TEXT NOT NULL,
    last_seen_run_id INTEGER NOT NULL,
    last_seen_at_utc TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    consecutive_misses INTEGER NOT NULL DEFAULT 0,
    missing_since_at_utc TEXT,
    closed_at_utc TEXT,
    reopen_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (first_seen_run_id) REFERENCES runs(id),
    FOREIGN KEY (last_seen_run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS unidentifiable_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL,
    raw_item TEXT NOT NULL,
    reason TEXT NOT NULL,
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
"""


def utc_now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class Store:
    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.raw_dir = self.data_dir / RAW_DIRNAME
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.data_dir / DB_FILENAME)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.raw_decode_errors = 0

    def __enter__(self) -> Store:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is None:
            self.conn.commit()
        self.conn.close()

    # -- raw JSONL log -----------------------------------------------------

    def write_raw(self, run_uuid, fetched_at, http_status, body, network_error) -> None:
        """Append one line for this run attempt. Called before any parsing.

        Fsynced: a run happens once per 30 minutes, so the extra syscall cost
        is irrelevant, and this is the durability point the rest of the design
        depends on - a crash or power loss right after this call must not lose
        the response.
        """
        date_part = fetched_at[:10].replace("-", "")
        path = self.raw_dir / f"messages-{date_part}.jsonl"
        line = json.dumps(
            {
                "run_uuid": run_uuid,
                "fetched_at_utc": fetched_at,
                "http_status": http_status,
                "body": body,
                "network_error": network_error,
            },
            sort_keys=True,
        )
        with path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
            f.flush()
            os.fsync(f.fileno())

    def iter_raw_lines(self):
        """Yield every recorded run attempt, oldest file first, append order
        within a file. Never sorts by the embedded timestamp - a Pi's clock can
        jump (e.g. before NTP sync after a reboot), and replay must follow the
        order runs actually happened in, not a timestamp that might be wrong.

        An undecodable line is skipped and counted in self.raw_decode_errors
        rather than aborting the replay: write_raw's append is not atomic, so a
        power cut leaves a truncated last line, and one bad line must not make
        every good line behind it unreplayable.
        """
        self.raw_decode_errors = 0
        for path in sorted(self.raw_dir.glob("messages-*.jsonl")):
            with path.open("r", encoding="utf-8") as f:
                for lineno, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError as exc:
                        self.raw_decode_errors += 1
                        print(
                            f"warning: skipping unreadable line {path.name}:{lineno}: {exc}",
                            file=sys.stderr,
                        )
                        continue
                    yield record

    # -- runs ----------------------------------------------------------

    def record_run_failure(
        self, run_uuid, started_at, finished_at, outcome, http_status, error_detail, exit_code
    ) -> None:
        self.conn.execute(
            """INSERT INTO runs (
                run_uuid, started_at_utc, finished_at_utc, outcome, http_status,
                item_count, schema_drift_count, error_detail, exit_code
            ) VALUES (?, ?, ?, ?, ?, NULL, 0, ?, ?)""",
            (run_uuid, started_at, finished_at, outcome, http_status, error_detail, exit_code),
        )

    def begin_run_success(self, run_uuid, started_at, http_status) -> int:
        """Insert a placeholder row so message rows have a run_id to reference,
        then finalize_run() fills in the real outcome once diffing is done."""
        cur = self.conn.execute(
            """INSERT INTO runs (
                run_uuid, started_at_utc, finished_at_utc, outcome, http_status,
                item_count, schema_drift_count, error_detail, exit_code
            ) VALUES (?, ?, ?, 'ok', ?, 0, 0, NULL, 0)""",
            (run_uuid, started_at, started_at, http_status),
        )
        return cur.lastrowid

    def finalize_run(self, run_id, finished_at, item_count, schema_drift_count, exit_code) -> None:
        self.conn.execute(
            """UPDATE runs SET finished_at_utc = ?, item_count = ?,
               schema_drift_count = ?, exit_code = ? WHERE id = ?""",
            (finished_at, item_count, schema_drift_count, exit_code, run_id),
        )

    def reset_derived_tables(self) -> None:
        """Wipe everything derived from the raw log, ready for a replay.

        execute() rather than executescript(), which would commit the wipe
        immediately while the replay inserts still roll back on error - leaving
        an empty database behind after a failed rebuild. These stay in the
        caller's transaction, so a failed rebuild takes the wipe back with it.
        """
        self.conn.execute("DELETE FROM unidentifiable_items")
        self.conn.execute("DELETE FROM messages")
        self.conn.execute("DELETE FROM runs")

    # -- message lifecycle ---------------------------------------------

    def diff_and_update_messages(self, run_id: int, observed_at: str, items: list) -> dict:
        """Apply one run's items against current message state.

        This is the only place open/closed status changes. It is only ever
        reached for a run whose response parsed as a genuine JSON list (see
        poll.apply_response) - a failed or unparseable run never calls this,
        so it can never be misread as "zero messages" and close everything.
        """
        from . import parse

        present: dict[str, dict] = {}
        unidentifiable = 0
        duplicate_conflicts = 0

        for raw_item in items:
            valid, reason = parse.identity_fields_valid(raw_item)
            if not valid:
                self.conn.execute(
                    "INSERT INTO unidentifiable_items (run_id, raw_item, reason) VALUES (?, ?, ?)",
                    (run_id, json.dumps(raw_item), reason),
                )
                unidentifiable += 1
                continue
            key = parse.derive_identity_key(raw_item)
            if key in present:
                if present[key] != raw_item:
                    duplicate_conflicts += 1
                continue
            present[key] = raw_item

        new_count = 0
        reopened_count = 0
        closed_count = 0

        for key, raw_item in present.items():
            n = parse.normalize_item(raw_item)
            existing = self.conn.execute(
                "SELECT id, status FROM messages WHERE identity_key = ?", (key,)
            ).fetchone()
            if existing is None:
                self.conn.execute(
                    """INSERT INTO messages (
                        identity_key, head, text_raw, start_raw, start_utc, end_raw, end_utc,
                        location_codes, products, event_stops, tz_ambiguous,
                        first_seen_run_id, first_seen_at_utc,
                        last_seen_run_id, last_seen_at_utc,
                        status, consecutive_misses, missing_since_at_utc,
                        closed_at_utc, reopen_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              'open', 0, NULL, NULL, 0)""",
                    (
                        key, n["head"], n["text_raw"], n["start_raw"], n["start_utc"],
                        n["end_raw"], n["end_utc"], n["location_codes"], n["products"],
                        n["event_stops"], n["tz_ambiguous"],
                        run_id, observed_at, run_id, observed_at,
                    ),
                )
                new_count += 1
            else:
                was_closed = existing["status"] == "closed"
                self.conn.execute(
                    """UPDATE messages SET
                        head = ?, text_raw = ?, start_raw = ?, start_utc = ?,
                        end_raw = ?, end_utc = ?,
                        location_codes = ?, products = ?, event_stops = ?, tz_ambiguous = ?,
                        last_seen_run_id = ?, last_seen_at_utc = ?,
                        status = 'open', consecutive_misses = 0, missing_since_at_utc = NULL,
                        closed_at_utc = CASE WHEN ? THEN NULL ELSE closed_at_utc END,
                        reopen_count = reopen_count + ?
                       WHERE id = ?""",
                    (
                        n["head"], n["text_raw"], n["start_raw"], n["start_utc"],
                        n["end_raw"], n["end_utc"],
                        n["location_codes"], n["products"], n["event_stops"], n["tz_ambiguous"],
                        run_id, observed_at,
                        1 if was_closed else 0,
                        1 if was_closed else 0,
                        existing["id"],
                    ),
                )
                if was_closed:
                    reopened_count += 1

        raw_grace = os.environ.get("LIFT_STATUS_GRACE_MISSES", "1")
        try:
            grace = max(1, int(raw_grace))
        except ValueError:
            # A typo in the env file must not stop collection dead here, after
            # write_raw and before any alert path.
            print(
                f"warning: LIFT_STATUS_GRACE_MISSES={raw_grace!r} is not a number; using 1",
                file=sys.stderr,
            )
            grace = 1
        open_rows = self.conn.execute(
            "SELECT id, identity_key, consecutive_misses, missing_since_at_utc "
            "FROM messages WHERE status = 'open'"
        ).fetchall()
        for row in open_rows:
            if row["identity_key"] in present:
                continue
            missing_since = row["missing_since_at_utc"] or observed_at
            misses = row["consecutive_misses"] + 1
            if misses >= grace:
                self.conn.execute(
                    """UPDATE messages SET status = 'closed', consecutive_misses = ?,
                       missing_since_at_utc = ?, closed_at_utc = ? WHERE id = ?""",
                    (misses, missing_since, missing_since, row["id"]),
                )
                closed_count += 1
            else:
                self.conn.execute(
                    "UPDATE messages SET consecutive_misses = ?, missing_since_at_utc = ? "
                    "WHERE id = ?",
                    (misses, missing_since, row["id"]),
                )

        return {
            "new": new_count,
            "closed": closed_count,
            "reopened": reopened_count,
            "unidentifiable": unidentifiable,
            "duplicate_conflicts": duplicate_conflicts,
        }

    # -- reporting -------------------------------------------------------

    def stats(self) -> dict:
        def one(sql):
            return self.conn.execute(sql).fetchone()[0]

        total = one("SELECT COUNT(*) FROM messages")
        open_n = one("SELECT COUNT(*) FROM messages WHERE status = 'open'")
        reopened_n = one("SELECT COUNT(*) FROM messages WHERE reopen_count > 0")
        unidentifiable_n = one("SELECT COUNT(*) FROM unidentifiable_items")
        runs_n = one("SELECT COUNT(*) FROM runs")
        first_run = one("SELECT MIN(started_at_utc) FROM runs")
        last_run = one("SELECT MAX(started_at_utc) FROM runs")
        by_outcome = self.conn.execute(
            "SELECT outcome, COUNT(*) FROM runs GROUP BY outcome ORDER BY outcome"
        ).fetchall()
        recent_runs = self.conn.execute(
            "SELECT started_at_utc, outcome, item_count, schema_drift_count "
            "FROM runs ORDER BY id DESC LIMIT 10"
        ).fetchall()
        db_path = self.data_dir / DB_FILENAME
        return {
            "messages_total": total,
            "open": open_n,
            "closed": total - open_n,
            "reopened": reopened_n,
            "unidentifiable": unidentifiable_n,
            "runs": runs_n,
            "first_run": first_run,
            "last_run": last_run,
            "by_outcome": [(r[0], r[1]) for r in by_outcome],
            "db_bytes": db_path.stat().st_size if db_path.exists() else 0,
            "raw_bytes": sum(p.stat().st_size for p in self.raw_dir.glob("messages-*.jsonl")),
            "recent_runs": [dict(r) for r in recent_runs],
        }
