"""Failure signalling.

Failures are pushed to LIFT_STATUS_ALERT_WEBHOOK, and the exit code carries the
same information for whatever is running the collector. Since this project's
whole failure mode is stopping silently while messages come and go unrecorded,
an alert has to stand on its own: what broke, and what to do about it. Nobody
reading one of these has the context of this repository in front of them.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

EXIT_OK = 0
EXIT_AUTH = 2
EXIT_UNREACHABLE = 3
EXIT_SCHEMA_DRIFT = 4
EXIT_STORAGE = 6

EXIT_MEANINGS = {
    EXIT_OK: "success",
    EXIT_AUTH: "API key rejected",
    EXIT_UNREACHABLE: "messages API unreachable",
    EXIT_SCHEMA_DRIFT: "API response shape changed",
    EXIT_STORAGE: "data directory not writable",
}

BANNER_WIDTH = 78

# How long before an unchanged banner is worth pushing again.
ALERT_REPEAT_SECONDS = 24 * 60 * 60


def banner(title: str, lines: list[str]) -> str:
    bar = "!" * BANNER_WIDTH
    out = [bar, f"!!! {title}", bar, ""]
    out.extend(line for line in lines if line is not None)
    out.append("")
    return "\n".join(out)


def auth_banner(masked_key: str, detail: str = "") -> str:
    # The single most important banner in this project: the user expects the
    # key to rotate with no known cadence, and there is no supported way to
    # obtain a new one other than re-capturing it from a browser.
    return banner(
        "LIFT-STATUS FATAL: API KEY REJECTED",
        [
            f"The key currently in use ({masked_key}) is no longer accepted.",
            "No message data is being collected. Any lift-outage message that",
            "opens or closes while this is broken will be invisible in the",
            "history - there is no way to recover it after the fact.",
            "",
            "To fix:",
            "  1. Open https://www.irishrail.ie in a browser (Safari or Chrome).",
            "  2. Open developer tools -> Network tab, and reload the page or",
            "     navigate to a page that shows service messages/disruptions.",
            "  3. Find a request to connect.irishrail.ie/realtime/messages",
            "     and copy the value of the 'x-api-key' request header.",
            "  4. Set LIFT_STATUS_API_KEY to it in /etc/lift-status.env",
            "  5. Confirm it works:  sudo lift check",
            "  6. Restart the timer if it isn't already running:",
            "       sudo systemctl restart lift-status.timer",
            "",
            f"Raw error: {detail}" if detail else "",
        ],
    )



def missing_key_banner() -> str:
    """Separate from auth_banner because the fix differs: nothing to
    re-capture, the env file simply has no key in it."""
    return banner(
        "LIFT-STATUS FATAL: NO API KEY CONFIGURED",
        [
            "LIFT_STATUS_API_KEY is not set, so no request was even attempted.",
            "No message data is being collected.",
            "",
            "The key is not stored in this repository on purpose. To set it:",
            "  1. Open https://www.irishrail.ie in a browser (Safari or Chrome).",
            "  2. Open developer tools -> Network tab, and reload the page or",
            "     navigate to a page that shows service messages/disruptions.",
            "  3. Find a request to connect.irishrail.ie/realtime/messages",
            "     and copy the value of the 'x-api-key' request header.",
            "  4. Add it to /etc/lift-status.env as:",
            "       LIFT_STATUS_API_KEY=<the value you copied>",
            "  5. Confirm it works:  sudo lift check",
        ],
    )

def unreachable_banner(detail: str) -> str:
    return banner(
        "LIFT-STATUS: API UNREACHABLE",
        [
            "The messages endpoint could not be reached after retries.",
            "If this clears on the next run, no action is needed - a single",
            "missed cycle is a small gap in the history. Repeated failures",
            "mean messages are opening and closing without being recorded.",
            "",
            f"Raw error: {detail}",
        ],
    )


def schema_root_banner() -> str:
    return banner(
        "LIFT-STATUS: API SHAPE CHANGED",
        [
            "The response no longer parses as a plain JSON list of messages.",
            "The raw response was still written to the JSONL log verbatim, so",
            "no data has been lost. Update lift_status/parse.py to handle the",
            "new shape, then run 'rebuild' to re-derive the database.",
        ],
    )


def schema_banner(problems: list[str]) -> str:
    return banner(
        "LIFT-STATUS: MESSAGE SCHEMA CHANGED",
        [
            "Some messages had fields this collector does not recognise:",
            *[f"  - {p}" for p in problems],
            "",
            "Raw responses were still written to the JSONL log verbatim, so no",
            "data has been lost. Update lift_status/parse.py to handle the new",
            "shape, then run 'rebuild' to re-derive the database.",
        ],
    )


def storage_banner(data_dir, problem: str) -> str:
    return banner(
        "LIFT-STATUS: DATA DIRECTORY NOT WRITABLE",
        [
            f"{problem}",
            "",
            "Nothing was collected. Usual causes are a full SD card, or the",
            "directory not being owned by the user the collector runs as.",
            "",
            "Check:",
            f"  df -h {data_dir}",
            f"  ls -ld {data_dir}",
            "  sudo chown -R lift-status:lift-status /var/lib/lift-status",
        ],
    )


def _marker_path() -> Path:
    state_dir = os.environ.get("LIFT_STATUS_DATA_DIR") or tempfile.gettempdir()
    return Path(state_dir) / ".last-alert.json"


def _digest(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()


def _suppressed(message: str) -> bool:
    """True if this exact banner was already *delivered* within the repeat window.

    A stuck condition would otherwise push every 30 minutes until someone
    patches the code, teaching the user to mute the topic. Best-effort: any
    problem reading the marker means send.
    """
    try:
        state = json.loads(_marker_path().read_text(encoding="utf-8"))
        sent_at = float(state.get("sent_at", 0))
        if state.get("digest") == _digest(message) and time.time() - sent_at < ALERT_REPEAT_SECONDS:
            return True
    except (OSError, ValueError, TypeError, AttributeError):
        # AttributeError: the file parsed but is not an object (`null`, a list,
        # a bare string), so .get is not there. Best-effort means send, not die
        # here - notify()'s own guard starts after this call.
        pass
    return False


def _mark_delivered(message: str) -> None:
    """Start the repeat window, and only once the webhook has actually taken it.

    Writing this on the attempt instead silences the next 24 hours on a webhook
    blip, which lands hardest at the only moment that matters: the first alert
    of a collector that has stopped.
    """
    try:
        _marker_path().write_text(
            json.dumps({"digest": _digest(message), "sent_at": time.time()}), encoding="utf-8"
        )
    except OSError:
        pass


def notify(message: str, dedup: bool = True) -> bool:
    """Push to LIFT_STATUS_ALERT_WEBHOOK. Returns whether it was delivered.

    Best-effort by design: a webhook failure must never mask the underlying
    problem or change the exit code. An unchanged banner is suppressed for
    ALERT_REPEAT_SECONDS unless dedup=False (test-alert always sends).
    """
    url = os.environ.get("LIFT_STATUS_ALERT_WEBHOOK")
    if not url:
        return False
    if dedup and _suppressed(message):
        return False
    try:
        if "ntfy" in url:
            data, headers = message.encode("utf-8"), {"Title": "lift-status failure"}
        else:
            data = json.dumps({"content": message, "text": message}).encode("utf-8")
            headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        urllib.request.urlopen(req, timeout=10).close()
        if dedup:
            _mark_delivered(message)
        return True
    except Exception as exc:  # pragma: no cover - never let alerting break the run
        print(f"warning: alert webhook failed: {exc}", file=sys.stderr)
        return False


def fail(message: str, code: int) -> int:
    """Print a fatal banner to stderr, fire the optional webhook, return the code."""
    print(message, file=sys.stderr)
    notify(message)
    return code
