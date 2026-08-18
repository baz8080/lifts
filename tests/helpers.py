"""Shared test helpers. No mocking framework - just small fakes."""

from __future__ import annotations

from lift_status.client import MessagesError


def make_item(
    head="Test Station - Lift out of order",
    text="The lift is out of service.",
    start="2026-01-01T00:00:00",
    end="2026-12-31T23:59:00",
    codes=None,
    products=None,
    event_stops=None,
):
    return {
        "head": head,
        "text": text,
        "start": start,
        "end": end,
        "locationCodes": codes if codes is not None else ["TEST"],
        "products": products if products is not None else ["Train"],
        "eventStops": event_stops if event_stops is not None else [
            {"sStop": "Test Station", "eStop": "Test Station", "direction": "1"}
        ],
    }


class FakeClient:
    """Stands in for MessagesClient in poll.py tests.

    `responses` is a list of either (http_status, body_text) tuples, for a
    successful fetch, or MessagesError instances to be raised - one consumed
    per call to get_messages_raw().
    """

    def __init__(self, responses, api_key="fake-key-xxxxxxxxxxxxxxxx"):
        self._responses = list(responses)
        self.api_key = api_key
        self.calls = 0

    @property
    def masked_key(self) -> str:
        if not self.api_key:
            return "<unset>"
        return f"{self.api_key[:6]}...{self.api_key[-4:]}"

    def get_messages_raw(self) -> tuple[int, str]:
        self.calls += 1
        item = self._responses.pop(0)
        if isinstance(item, MessagesError):
            raise item
        return item

    def get_messages(self):
        import json

        status, body = self.get_messages_raw()
        return json.loads(body)
