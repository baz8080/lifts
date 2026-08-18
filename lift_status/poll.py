"""One collection run, and the replay logic `rebuild` uses to recreate the DB.

Ordering in a live run is deliberate: the response is written to the raw log
before any parsing begins, so a crash, a Pi power loss, or an OOM kill halfway
through still leaves a durable record of exactly what the API said.

The single most important structural property of this module: a failed or
unparseable response can never reach `store.diff_and_update_messages`, the
only function that changes a message's open/closed status. Every failure path
below returns before that point. This is what stops "the fetch failed" from
ever being misread as "the list came back empty" - which would otherwise mark
every currently-open message as fixed.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from . import alert
from .client import ApiError, AuthError, MessagesClient, TransientError
from .parse import NOT_A_LIST, check_item_schema, parse_top_level
from .store import Store, utc_now_iso


@dataclass
class ApplyResult:
    outcome: str
    exit_code: int
    http_status: int | None
    error_detail: str | None = None
    item_count: int | None = None
    schema_drift_count: int = 0
    drift_problems: list[str] = field(default_factory=list)
    diff: dict | None = None


def apply_response(
    store: Store, run_uuid: str, fetched_at: str, http_status, body_text, network_error
) -> ApplyResult:
    """Classify one raw response and, only if it's genuinely usable, diff it.

    Used identically by a live poll run and by `rebuild` replaying the JSONL
    log, so the two can never classify the same response differently.
    """

    def failed(outcome, detail, exit_code):
        store.record_run_failure(
            run_uuid, fetched_at, fetched_at, outcome, http_status, detail, exit_code
        )
        return ApplyResult(
            outcome=outcome, exit_code=exit_code, http_status=http_status, error_detail=detail
        )

    if http_status is None or http_status >= 400 or body_text is None:
        # Either a true network-level failure (no response at all) or an HTTP
        # error status. auth_error is split out because it needs a distinct,
        # much louder alert; every other error status is folded into
        # "unreachable" since the practical outcome is identical either way -
        # nothing was collected this run.
        #
        # A sub-400 status does not imply a body: urllib does not follow a 300
        # or 304, so those arrive as ApiError with no body, and a None body
        # reaching json.loads() would crash past every alert path.
        outcome = "auth_error" if http_status in (401, 403) else "unreachable"
        exit_code = alert.EXIT_AUTH if outcome == "auth_error" else alert.EXIT_UNREACHABLE
        detail = network_error or f"HTTP {http_status}"
        return failed(outcome, detail, exit_code)

    try:
        parsed = parse_top_level(body_text)
    except json.JSONDecodeError as exc:
        return failed("parse_error", f"malformed JSON: {exc}", alert.EXIT_SCHEMA_DRIFT)

    if parsed is NOT_A_LIST:
        return failed("not_a_list", "response root is not a JSON list", alert.EXIT_SCHEMA_DRIFT)

    items = parsed
    drift_by_item = {i: check_item_schema(item) for i, item in enumerate(items)}
    drift_by_item = {i: p for i, p in drift_by_item.items() if p}
    drift_problems = sorted({p for problems in drift_by_item.values() for p in problems})
    exit_code = alert.EXIT_SCHEMA_DRIFT if drift_by_item else alert.EXIT_OK

    run_id = store.begin_run_success(run_uuid, fetched_at, http_status)
    diff = store.diff_and_update_messages(run_id, fetched_at, items)
    store.finalize_run(run_id, fetched_at, len(items), len(drift_by_item), exit_code)

    return ApplyResult(
        outcome="ok",
        exit_code=exit_code,
        http_status=http_status,
        item_count=len(items),
        schema_drift_count=len(drift_by_item),
        drift_problems=drift_problems,
        diff=diff,
    )


@contextlib.contextmanager
def poll_lock(data_dir: Path):
    """Exclusive lock so two runs can never interleave writes.

    A contended run yields False and its caller writes nothing at all - not
    even a `runs` row - so a skipped cycle can never be misread as a real
    "zero messages" run.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    lock_path = data_dir / ".poll.lock"
    handle = lock_path.open("w")
    try:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            yield False
            return
        yield True
    finally:
        handle.close()


def check_writable(data_dir: Path) -> str | None:
    """Return a human explanation if the data directory is unusable, else None."""
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return f"cannot create {data_dir}: {exc}"
    probe = data_dir / ".write-test"
    try:
        probe.touch()
        probe.unlink()
    except OSError as exc:
        return f"cannot write inside {data_dir}: {exc}"
    return None


def run_poll(data_dir, client: MessagesClient | None = None) -> int:
    client = client or MessagesClient()
    data_dir = Path(data_dir)

    problem = check_writable(data_dir)
    if problem:
        return alert.fail(alert.storage_banner(data_dir, problem), alert.EXIT_STORAGE)

    # Before the fetch, so this writes nothing: a keyless request would come
    # back 401 and be recorded as a rejected key, sending the user off to
    # re-capture a key that was never configured.
    if not client.api_key:
        return alert.fail(alert.missing_key_banner(), alert.EXIT_AUTH)

    with poll_lock(data_dir) as acquired:
        if not acquired:
            print("another poll run holds the lock; skipping this trigger")
            return alert.EXIT_OK
        return _run(data_dir, client)


def _run(data_dir: Path, client: MessagesClient) -> int:
    run_uuid = str(uuid.uuid4())
    fetched_at = utc_now_iso()

    try:
        http_status, body_text = client.get_messages_raw()
        network_error = None
    except (AuthError, TransientError, ApiError) as exc:
        http_status = exc.status
        body_text = None
        network_error = repr(exc)

    with Store(data_dir) as store:
        store.write_raw(run_uuid, fetched_at, http_status, body_text, network_error)
        result = apply_response(store, run_uuid, fetched_at, http_status, body_text, network_error)

    if result.outcome == "auth_error":
        banner = alert.auth_banner(client.masked_key, result.error_detail or "")
        return alert.fail(banner, result.exit_code)
    if result.outcome == "unreachable":
        return alert.fail(alert.unreachable_banner(result.error_detail or ""), result.exit_code)
    if result.outcome in ("parse_error", "not_a_list"):
        return alert.fail(alert.schema_root_banner(), result.exit_code)

    diff = result.diff or {}
    print(
        f"run {fetched_at}: {result.item_count} messages listed, "
        f"{diff.get('new', 0)} new, {diff.get('closed', 0)} closed, "
        f"{diff.get('reopened', 0)} reopened, {diff.get('unidentifiable', 0)} unidentifiable, "
        f"{diff.get('duplicate_conflicts', 0)} duplicate conflicts"
    )
    if result.schema_drift_count:
        return alert.fail(alert.schema_banner(result.drift_problems), result.exit_code)
    return alert.EXIT_OK


def run_check(client: MessagesClient | None = None) -> int:
    """Validate connectivity and the API key without writing anything.

    Safe to run at any time, including while a poll is in progress, since it
    takes no lock and touches no files.
    """
    client = client or MessagesClient()
    if not client.api_key:
        return alert.fail(alert.missing_key_banner(), alert.EXIT_AUTH)
    try:
        items = client.get_messages()
    except AuthError as exc:
        return alert.fail(alert.auth_banner(client.masked_key, str(exc)), alert.EXIT_AUTH)
    except (TransientError, ApiError) as exc:
        return alert.fail(alert.unreachable_banner(str(exc)), alert.EXIT_UNREACHABLE)

    if not isinstance(items, list):
        return alert.fail(alert.schema_root_banner(), alert.EXIT_SCHEMA_DRIFT)

    print(f"ok: key {client.masked_key} accepted, {len(items)} messages currently listed")
    return alert.EXIT_OK


def run_rebuild(data_dir) -> int:
    """Wipe the derived DB and replay it from the raw JSONL log.

    Safe by design: the raw log is the source of truth, so this can be run
    after a parse.py bug fix to re-derive correct history, or after any
    suspicion the database doesn't match the log.

    Takes the poll lock: otherwise the wipe-and-replay races the 30-minute
    timer, either locking the poll out of the database or erasing a run it has
    just committed.
    """
    data_dir = Path(data_dir)
    count = 0
    with poll_lock(data_dir) as acquired:
        if not acquired:
            print(
                "a poll run holds the lock; nothing was rebuilt - try again in a moment",
                file=sys.stderr,
            )
            return 1
        with Store(data_dir) as store:
            store.reset_derived_tables()
            for record in store.iter_raw_lines():
                apply_response(
                    store,
                    record["run_uuid"],
                    record["fetched_at_utc"],
                    record.get("http_status"),
                    record.get("body"),
                    record.get("network_error"),
                )
                count += 1
            skipped = store.raw_decode_errors
    print(f"rebuilt from {count} recorded run(s)")
    if skipped:
        print(
            f"warning: skipped {skipped} unreadable raw line(s), listed above",
            file=sys.stderr,
        )
    if count == 0:
        print("nothing to replay: no raw logs found")
    return alert.EXIT_OK
