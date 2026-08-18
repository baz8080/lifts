"""Normalisation of Irish Rail message payloads.

Every function here is pure and total: it never raises on odd input, it
returns what it could parse plus a flag or a problem list. The raw response is
always written to the JSONL log before any of this runs, so a bug here costs
nothing that `rebuild` cannot fix later.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

# The full field set of a message, as observed live. Anything added or removed
# trips schema-drift detection, because a silently changed API is how a
# collector rots without anyone noticing. Drift on these fields is soft (logged,
# not fatal) - see identity_fields_valid() below for the fields that ARE fatal
# for an individual item.
KNOWN_FIELDS = frozenset(
    {"head", "text", "start", "end", "locationCodes", "products", "eventStops"}
)

# The fields the identity key is built from. Missing/malformed here makes an
# item impossible to track safely - it is routed to unidentifiable_items
# instead of participating in open/closed tracking at all.
IDENTITY_FIELDS = ("head", "locationCodes", "start")

# The messages endpoint has no UTC offset on its timestamps, same problem as
# other Irish transport APIs of this vintage. Treated as Dublin wall-clock time.
DUBLIN = ZoneInfo("Europe/Dublin")
DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"


class NotAList:
    """Sentinel: the response parsed as JSON but its root wasn't a list.

    Deliberately not `None` or `[]` - either of those could be produced by an
    honest empty response too, and conflating "couldn't understand this" with
    "genuinely zero items" is exactly the bug this whole project is designed to
    avoid (see poll.py).
    """


NOT_A_LIST = NotAList()


def parse_top_level(body_text: str):
    """Parse the raw response body.

    Returns a list of items, or NOT_A_LIST if the JSON root isn't a list.
    Raises json.JSONDecodeError if the body isn't valid JSON at all - callers
    must treat that as a hard failure, same as NOT_A_LIST.
    """
    data = json.loads(body_text)
    if not isinstance(data, list):
        return NOT_A_LIST
    return data


def check_item_schema(item) -> list[str]:
    """Return human-readable descriptions of any drift from the known shape."""
    if not isinstance(item, dict):
        return ["item is not an object"]
    keys = set(item)
    problems = []
    unexpected = sorted(keys - KNOWN_FIELDS)
    missing = sorted(KNOWN_FIELDS - keys)
    if unexpected:
        problems.append(f"unexpected field(s): {', '.join(unexpected)}")
    if missing:
        problems.append(f"missing field(s): {', '.join(missing)}")
    return problems


def identity_fields_valid(item) -> tuple[bool, str | None]:
    """Check the three fields the identity key depends on.

    An item failing this check is excluded from open/closed tracking entirely
    (see store.diff_and_update_messages) rather than aborting the whole run -
    one malformed banner among many shouldn't block tracking of the rest.
    """
    if not isinstance(item, dict):
        return False, "item is not an object"
    head = item.get("head")
    start = item.get("start")
    codes = item.get("locationCodes")
    if not isinstance(head, str) or not head.strip():
        return False, "head is missing or not a non-empty string"
    if not isinstance(start, str) or not start.strip():
        return False, "start is missing or not a non-empty string"
    if not isinstance(codes, list) or not codes or not all(
        isinstance(c, str) and c.strip() for c in codes
    ):
        return False, "locationCodes is missing, empty, or not a list of strings"
    return True, None


def derive_identity_key(item: dict) -> str:
    """Synthesize a stable key from head + sorted locationCodes + start.

    There is no ID field in this API at all, unlike list-endpoint items
    elsewhere that at least have a stub identifier. Location codes are
    case/whitespace-normalized and sorted since they're codes, not prose, so
    reordering or casing differences between runs can't fracture the key.
    `head` and `start` are compared verbatim: an editorial edit to the message
    text or a corrected start time will produce a new key, which looks like the
    old message closing and a new one opening. This is an accepted limitation
    (see the project README) rather than something this function tries to
    paper over - the raw JSONL log keeps everything needed to reprocess with
    smarter matching later if it turns out to matter in practice.

    Caller must have already checked identity_fields_valid(item).
    """
    head = item["head"].strip()
    start = item["start"].strip()
    codes = sorted(c.strip().upper() for c in item["locationCodes"])
    payload = "\x1f".join([head, ",".join(codes), start])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def parse_dublin_datetime(value) -> tuple[str | None, bool]:
    """Parse 'YYYY-MM-DDTHH:MM:SS' Dublin local time into an ISO8601 UTC string.

    Returns (utc_iso_or_None, tz_ambiguous). The flag is set when the wall-clock
    time is ambiguous or impossible because of a DST transition:

    - Fall back (last Sunday of October): 01:00-01:59 happens twice. We take
      the first occurrence (fold=0), so the value may be an hour late.
    - Spring forward (last Sunday of March): 01:00-01:59 never happens. Python
      resolves it, but the result is a fiction.

    Either way the raw string is retained in the database, so a flagged row can
    be revisited rather than silently trusted. This value is used only for
    display/reporting on start/end - closure detection never depends on it (see
    poll.py, which timestamps runs with datetime.now(timezone.utc) only).
    """
    if not isinstance(value, str) or not value.strip():
        return None, False
    try:
        naive = datetime.strptime(value.strip(), DATETIME_FORMAT)
    except ValueError:
        return None, False

    local = naive.replace(tzinfo=DUBLIN)

    ambiguous = local.utcoffset() != local.replace(fold=1).utcoffset()
    roundtrip = local.astimezone(timezone.utc).astimezone(DUBLIN)
    imaginary = roundtrip.replace(tzinfo=None) != naive

    utc = local.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%SZ"), bool(ambiguous or imaginary)


def _text(value):
    """Normalise empty-string sentinels to NULL, keeping real text."""
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)


def _json_or_none(value):
    return json.dumps(value) if value is not None else None


def normalize_item(item: dict) -> dict:
    """Turn a raw message item into the column set stored in SQLite.

    Caller must have already checked identity_fields_valid(item). Fields
    outside the known set are not included here - check_item_schema already
    flagged them as drift, and the raw JSONL log keeps them verbatim regardless.
    """
    start_utc, start_amb = parse_dublin_datetime(item.get("start"))
    end_utc, end_amb = parse_dublin_datetime(item.get("end"))
    codes = sorted(c.strip().upper() for c in item["locationCodes"])

    return {
        "head": item["head"].strip(),
        "text_raw": _text(item.get("text")),
        "start_raw": item["start"].strip(),
        "start_utc": start_utc,
        "end_raw": _text(item.get("end")),
        "end_utc": end_utc,
        "location_codes": json.dumps(codes),
        "products": _json_or_none(item.get("products")),
        "event_stops": _json_or_none(item.get("eventStops")),
        "tz_ambiguous": int(bool(start_amb or end_amb)),
    }
