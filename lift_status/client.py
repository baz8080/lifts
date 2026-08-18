"""HTTP client for Irish Rail's realtime service-message endpoint.

Stdlib only, deliberately: this has to run unattended on a Pi for years, and
every dependency is a future breakage. The error taxonomy here drives the
process exit code and the alert that gets pushed, so the distinctions it draws
are the ones a human will be woken by.

Unlike a paginated or list+detail API, this endpoint returns everything needed
in a single response, so there is exactly one HTTP call per poll run.
"""

from __future__ import annotations

import gzip
import http.client
import json
import os
import random
import socket
import time
import urllib.error
import urllib.request

URL = "https://connect.irishrail.ie/realtime/messages?lang=en"

# The key is not embedded here: it is Irish Rail's credential, and a key in a
# public repo is published to everyone who reads it. Supplied at runtime via
# LIFT_STATUS_API_KEY. Irish Rail rotates it without notice, which is why
# AuthError below is wired to the loudest alert this project has.

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/26.6 Safari/605.1.15"
)

# Origin/Referer are sent because some APIs validate them server-side as a
# second, weaker check alongside the key, not only via browser-enforced CORS.
ORIGIN = "https://www.irishrail.ie"
REFERER = "https://www.irishrail.ie/"

DEFAULT_TIMEOUT = 15.0
DEFAULT_RETRIES = 3


class MessagesError(Exception):
    """Base for all API errors.

    Carries the HTTP status code when the server actually responded (even with
    an error), or None for a network-level failure with no response at all.
    poll.py writes this straight into the raw JSONL line, so `rebuild` can
    re-derive the same classification later from (http_status, network_error)
    alone, without needing to re-catch a live exception.
    """

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


class AuthError(MessagesError):
    """HTTP 401/403 - the API key was rejected or missing.

    Never retried: a rejected key will not start working on the next attempt.
    """


class TransientError(MessagesError):
    """Network failure, timeout, or 5xx. Retried with backoff."""


class ApiError(MessagesError):
    """Any other unexpected HTTP status, or a response that isn't valid JSON."""


def _decode(raw: bytes, headers) -> str:
    """Decode a response body, honouring Content-Encoding regardless of what
    Accept-Encoding was sent (mirrors the ESB collector's defensive decode -
    some APIs gzip every response and ignore the request header entirely)."""
    encoding = (headers.get("Content-Encoding") or "").lower()
    if "gzip" in encoding:
        raw = gzip.decompress(raw)
    return raw.decode("utf-8")


class MessagesClient:
    def __init__(
        self,
        api_key: str | None = None,
        url: str = URL,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        sleep=time.sleep,
    ):
        self.api_key = api_key or os.environ.get("LIFT_STATUS_API_KEY") or ""
        self.url = url
        self.timeout = timeout
        self.retries = retries
        self._sleep = sleep

    @property
    def masked_key(self) -> str:
        k = self.api_key
        if not k:
            return "<unset>"
        if len(k) <= 10:
            return "***"
        return f"{k[:6]}...{k[-4:]}"

    def _request(self) -> tuple[int, str]:
        req = urllib.request.Request(
            self.url,
            headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
                "Origin": ORIGIN,
                "Referer": REFERER,
                "x-api-key": self.api_key,
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, _decode(resp.read(), resp.headers)
        except urllib.error.HTTPError as exc:
            body = ""
            try:
                body = _decode(exc.read(), exc.headers)
            except Exception:  # pragma: no cover - body is best-effort context
                pass
            if exc.code in (401, 403):
                raise AuthError(f"{exc.code} rejected key {self.masked_key}: {body}", status=exc.code) from exc
            if exc.code >= 500:
                raise TransientError(f"{exc.code} from {self.url}: {body}", status=exc.code) from exc
            raise ApiError(f"{exc.code} from {self.url}: {body}", status=exc.code) from exc
        except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as exc:
            raise TransientError(f"network failure for {self.url}: {exc}", status=None) from exc
        # IncompleteRead/BadStatusLine are HTTPException, and UnicodeDecodeError
        # from _decode is a ValueError - neither is an OSError, so without these
        # two clauses they escape _run and the attempt is never logged at all.
        except http.client.HTTPException as exc:
            raise TransientError(f"broken response from {self.url}: {exc!r}", status=None) from exc
        except UnicodeDecodeError as exc:
            raise ApiError(f"undecodable (non-UTF-8) body from {self.url}: {exc}", status=None) from exc

    def get_messages_raw(self) -> tuple[int, str]:
        """Return (http_status, raw_body_text), retrying transient failures.

        Returns the raw text rather than parsed JSON: the caller must write the
        response to the durable raw log verbatim before anything else happens,
        including before it is known whether the body is valid JSON.
        """
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                return self._request()
            except TransientError as exc:
                last = exc
                if attempt < self.retries - 1:
                    # Jitter so a Pi rebooting mid-incident doesn't sync up
                    # with anything else retrying against the same endpoint.
                    self._sleep(2**attempt + random.random())
        raise last  # type: ignore[misc]

    def get_messages(self) -> list:
        """Convenience wrapper used by `check`: fetch and parse in one step.

        Not used by `poll`, which needs the raw text for the durability write
        before parsing is attempted.
        """
        _status, body_text = self.get_messages_raw()
        try:
            return json.loads(body_text)
        except json.JSONDecodeError as exc:
            raise ApiError(f"malformed JSON from {self.url}: {exc}") from exc
