import io
import socket
import unittest
import urllib.error
from unittest import mock

from lift_status.client import AuthError, MessagesClient, TransientError


def _http_error(code, body=b"{}"):
    return urllib.error.HTTPError(
        url="https://connect.irishrail.ie/realtime/messages",
        code=code,
        msg="error",
        hdrs={},
        fp=io.BytesIO(body),
    )


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, headers=None):
        self._body = body
        self.status = status
        self.headers = headers or {}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class TestMessagesClient(unittest.TestCase):
    def test_successful_fetch_returns_status_and_body(self):
        client = MessagesClient(sleep=lambda s: None)
        with mock.patch("urllib.request.urlopen", return_value=FakeResponse(b"[]")):
            status, body = client.get_messages_raw()
        self.assertEqual(status, 200)
        self.assertEqual(body, "[]")

    def test_401_raises_auth_error_with_status(self):
        client = MessagesClient(sleep=lambda s: None)
        with mock.patch("urllib.request.urlopen", side_effect=_http_error(401)):
            with self.assertRaises(AuthError) as cm:
                client.get_messages_raw()
        self.assertEqual(cm.exception.status, 401)

    def test_403_raises_auth_error(self):
        client = MessagesClient(sleep=lambda s: None)
        with mock.patch("urllib.request.urlopen", side_effect=_http_error(403)):
            with self.assertRaises(AuthError) as cm:
                client.get_messages_raw()
        self.assertEqual(cm.exception.status, 403)

    def test_500_raises_transient_error_with_status(self):
        client = MessagesClient(retries=1, sleep=lambda s: None)
        with mock.patch("urllib.request.urlopen", side_effect=_http_error(500)):
            with self.assertRaises(TransientError) as cm:
                client.get_messages_raw()
        self.assertEqual(cm.exception.status, 500)

    def test_network_failure_raises_transient_error_with_no_status(self):
        client = MessagesClient(retries=1, sleep=lambda s: None)
        with mock.patch("urllib.request.urlopen", side_effect=socket.timeout("timed out")):
            with self.assertRaises(TransientError) as cm:
                client.get_messages_raw()
        self.assertIsNone(cm.exception.status)

    def test_retries_transient_before_succeeding(self):
        client = MessagesClient(retries=3, sleep=lambda s: None)
        calls = {"n": 0}

        def flaky(*a, **k):
            calls["n"] += 1
            if calls["n"] < 3:
                raise _http_error(503)
            return FakeResponse(b'[{"head": "ok"}]')

        with mock.patch("urllib.request.urlopen", side_effect=flaky):
            status, body = client.get_messages_raw()
        self.assertEqual(status, 200)
        self.assertEqual(calls["n"], 3)

    def test_masked_key_hides_the_middle(self):
        client = MessagesClient(api_key="AbCdEfGhIjKlMnOpQrStUvWxYz0123456789wxyz")
        self.assertEqual(client.masked_key, "AbCdEf...wxyz")
        self.assertNotIn("GhIjKlMnOpQrStUvWxYz0123456789", client.masked_key)

    def test_unset_key_is_reported_as_unset(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(MessagesClient().api_key, "")
            self.assertEqual(MessagesClient().masked_key, "<unset>")

    def test_env_var_supplies_the_key(self):
        with mock.patch.dict("os.environ", {"LIFT_STATUS_API_KEY": "from-the-env-file"}):
            self.assertEqual(MessagesClient().api_key, "from-the-env-file")

    def test_gzip_response_is_decoded_regardless_of_accept_encoding(self):
        import gzip

        compressed = gzip.compress(b"[]")
        resp = FakeResponse(compressed, headers={"Content-Encoding": "gzip"})
        client = MessagesClient(sleep=lambda s: None)
        with mock.patch("urllib.request.urlopen", return_value=resp):
            status, body = client.get_messages_raw()
        self.assertEqual(body, "[]")


if __name__ == "__main__":
    unittest.main()
