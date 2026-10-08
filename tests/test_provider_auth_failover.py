"""Issue #101: safe 401/403 classification + failover must not block unrelated jobs."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import worker_adapters
from scripts.provider_config import FailoverAdapter
from scripts.worker_adapters import (
    MissingCredential,
    MockAdapter,
    NonRetryableProviderError,
    ProviderAuthError,
    RetryableProviderError,
    _default_transport,
)

URL = "https://api.x.ai/v1/responses"
FAKE_TOKEN = "Bearer fake-test-token-value-not-real"
JOB = {"id": "job-auth-1", "project": "workspace", "objective": "unrelated task"}


def _http_error(code, body):
    raw = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
    return HTTPError(URL, code, "err", {"x-request-id": "req-secretish"}, io.BytesIO(raw))


def _call_with(exc):
    with mock.patch.object(worker_adapters, "urlopen", side_effect=exc):
        _default_transport(URL, {"Authorization": FAKE_TOKEN}, {"model": "m"}, 1.0)


class SafeHttpClassificationTests(unittest.TestCase):
    def test_403_is_auth_error_with_safe_fields_only(self):
        body = {"error": {"code": "permission_denied", "message": f"key {FAKE_TOKEN} user@example.com blocked"}}
        with self.assertRaises(ProviderAuthError) as ctx:
            _call_with(_http_error(403, body))
        exc = ctx.exception
        self.assertIsInstance(exc, NonRetryableProviderError)  # backward compatible
        self.assertEqual(exc.http_status, 403)
        self.assertEqual(exc.endpoint_host, "api.x.ai")
        self.assertEqual(exc.error_code, "permission_denied")
        self.assertFalse(exc.retryable)
        text = str(exc)
        self.assertTrue(text.startswith("provider HTTP 403"))  # grok_senses regex compat
        for leaked in ("fake-test-token", "example.com", "req-secretish", "/v1/responses", "blocked"):
            self.assertNotIn(leaked, text)

    def test_401_free_text_code_is_dropped(self):
        body = {"error": {"code": "has spaces and user@example.com"}}
        with self.assertRaises(ProviderAuthError) as ctx:
            _call_with(_http_error(401, body))
        self.assertIsNone(ctx.exception.error_code)
        self.assertNotIn("example.com", str(ctx.exception))

    def test_secret_like_code_is_dropped(self):
        body = {"error": {"code": "sk-" + "a" * 8}}
        with self.assertRaises(ProviderAuthError) as ctx:
            _call_with(_http_error(403, body))
        self.assertIsNone(ctx.exception.error_code)

    def test_403_non_json_body_is_safe(self):
        with self.assertRaises(ProviderAuthError) as ctx:
            _call_with(_http_error(403, b"<html>" + FAKE_TOKEN.encode() + b"</html>"))
        self.assertIsNone(ctx.exception.error_code)
        self.assertNotIn("fake-test-token", str(ctx.exception))

    def test_429_and_5xx_stay_retryable(self):
        for code in (429, 500, 503):
            with self.assertRaises(RetryableProviderError):
                _call_with(_http_error(code, {}))

    def test_400_is_non_retryable_but_not_auth(self):
        with self.assertRaises(NonRetryableProviderError) as ctx:
            _call_with(_http_error(400, {}))
        self.assertNotIsInstance(ctx.exception, ProviderAuthError)


class _Raising:
    def __init__(self, provider, exc):
        self.provider = provider
        self.exc = exc
        self.calls = 0

    def run(self, job):
        self.calls += 1
        raise self.exc


def _auth(host="api.x.ai"):
    return ProviderAuthError("provider HTTP 403 host=" + host, http_status=403, endpoint_host=host)


class FailoverAuthTests(unittest.TestCase):
    def test_grok_403_does_not_block_next_provider(self):
        gemini = _Raising("gemini", RetryableProviderError("provider HTTP 429"))
        grok = _Raising("grok", _auth())
        meta = MockAdapter(provider="meta", model="mock-meta")
        result = FailoverAdapter([gemini, grok, meta]).run(JOB)
        self.assertEqual(result["provider"], "meta")
        self.assertEqual(grok.calls, 1)  # tried once, no blind retry

    def test_all_auth_errors_raise_non_retryable(self):
        adapter = FailoverAdapter([_Raising("grok", _auth()), _Raising("meta", _auth("api.meta.ai"))])
        with self.assertRaises(ProviderAuthError):
            adapter.run(JOB)

    def test_mixed_auth_and_transient_stays_retryable(self):
        adapter = FailoverAdapter([_Raising("grok", _auth()), _Raising("openai", RetryableProviderError("503"))])
        with self.assertRaises(RetryableProviderError):
            adapter.run(JOB)

    def test_contract_errors_still_propagate(self):
        adapter = FailoverAdapter([_Raising("grok", NonRetryableProviderError("non-JSON")), MockAdapter()])
        with self.assertRaises(NonRetryableProviderError) as ctx:
            adapter.run(JOB)
        self.assertNotIsInstance(ctx.exception, ProviderAuthError)

    def test_missing_credential_behaviour_unchanged(self):
        adapter = FailoverAdapter([_Raising("grok", MissingCredential("missing"))])
        with self.assertRaises(RetryableProviderError):
            adapter.run(JOB)

    def test_auth_plus_missing_credential_is_non_retryable(self):
        grok = _Raising("grok", _auth())
        openai = _Raising("openai", MissingCredential("openai API credential is missing"))
        with self.assertRaises(ProviderAuthError) as ctx:
            FailoverAdapter([grok, openai]).run(JOB)
        self.assertFalse(ctx.exception.retryable)
        self.assertEqual(ctx.exception.http_status, 403)
        self.assertEqual(grok.calls, 1)

    def test_missing_credential_then_auth_order_is_non_retryable(self):
        adapter = FailoverAdapter([_Raising("gemini", MissingCredential("missing")), _Raising("grok", _auth())])
        with self.assertRaises(ProviderAuthError):
            adapter.run(JOB)

    def test_auth_missing_and_transient_stays_retryable(self):
        adapter = FailoverAdapter([
            _Raising("grok", _auth()),
            _Raising("openai", MissingCredential("missing")),
            _Raising("gemini", RetryableProviderError("provider HTTP 503")),
        ])
        with self.assertRaises(RetryableProviderError) as ctx:
            adapter.run(JOB)
        self.assertNotIsInstance(ctx.exception, ProviderAuthError)


if __name__ == "__main__":
    unittest.main()
