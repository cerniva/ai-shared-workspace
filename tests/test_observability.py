import os
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch


class ObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_emit_event_uses_sentry_when_configured(self):
        from scripts.observability import emit_event

        calls = {"init": [], "messages": []}
        fake = types.ModuleType("sentry_sdk")
        fake.init = lambda **kwargs: calls["init"].append(kwargs)
        fake.capture_message = lambda message, **kwargs: calls["messages"].append((message, kwargs))
        fake.capture_exception = lambda exc: None

        log_path = Path(self.tmp.name) / "events.jsonl"
        env = {
            "OBSERVABILITY_LOG_PATH": str(log_path),
            "SENTRY_DSN": "https://public@example.invalid/1",
        }
        with patch.dict(sys.modules, {"sentry_sdk": fake}):
            emit_event("worker.completed", {"job_id": "job-1", "worker": "grok"}, env=env)

        self.assertEqual(calls["init"][0]["dsn"], env["SENTRY_DSN"])
        self.assertEqual(len(calls["messages"]), 1)
        self.assertIn("worker.completed", calls["messages"][0][0])

    def test_sentry_exception_defaults_to_sanitized_message(self):
        from scripts.observability import emit_event

        calls = {"messages": [], "exceptions": []}
        fake = types.ModuleType("sentry_sdk")
        fake.init = lambda **kwargs: None
        fake.capture_message = lambda message, **kwargs: calls["messages"].append((message, kwargs))
        fake.capture_exception = lambda exc: calls["exceptions"].append(exc)

        secret_like = "sk-" + ("a" * 30)
        env = {"SENTRY_DSN": "https://public@example.invalid/2"}
        with patch.dict(sys.modules, {"sentry_sdk": fake}):
            emit_event(
                "worker.retryable_failed",
                {"job_id": "job-1", "error": f"temporary outage {secret_like}"},
                env=env,
                exception=RuntimeError(f"temporary outage {secret_like}"),
            )

        self.assertEqual(calls["exceptions"], [])
        self.assertEqual(len(calls["messages"]), 1)
        self.assertNotIn(secret_like, calls["messages"][0][0])
        self.assertIn("[REDACTED]", calls["messages"][0][0])

    def test_sentry_raw_exception_requires_explicit_opt_in(self):
        from scripts.observability import emit_event

        calls = {"messages": [], "exceptions": []}
        fake = types.ModuleType("sentry_sdk")
        fake.init = lambda **kwargs: None
        fake.capture_message = lambda message, **kwargs: calls["messages"].append((message, kwargs))
        fake.capture_exception = lambda exc: calls["exceptions"].append(exc)

        exception = RuntimeError("stack trace test without credentials")
        env = {
            "SENTRY_DSN": "https://public@example.invalid/3",
            "SENTRY_CAPTURE_RAW_EXCEPTIONS": "1",
        }
        with patch.dict(sys.modules, {"sentry_sdk": fake}):
            emit_event(
                "worker.retryable_failed",
                {"job_id": "job-1", "error": "stack trace test without credentials"},
                env=env,
                exception=exception,
            )

        self.assertEqual(calls["exceptions"], [exception])
        self.assertEqual(calls["messages"], [])

    def test_emit_event_uses_langfuse_when_configured(self):
        from scripts.observability import emit_event

        observations = []
        flushed = []

        class FakeClient:
            @contextmanager
            def start_as_current_observation(self, **kwargs):
                observations.append(kwargs)
                yield object()

            def flush(self):
                flushed.append(True)

        fake = types.ModuleType("langfuse")
        fake.get_client = lambda: FakeClient()

        env = {
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test-secret",
        }
        with patch.dict(os.environ, env, clear=False), patch.dict(sys.modules, {"langfuse": fake}):
            emit_event("worker.retryable_failed", {"job_id": "job-1", "error": "temporary outage"}, env=env)

        self.assertEqual(observations[0]["name"], "worker.retryable_failed")
        self.assertEqual(observations[0]["level"], "ERROR")
        self.assertEqual(observations[0]["metadata"]["job_id"], "job-1")
        self.assertEqual(flushed, [True])

    def test_missing_optional_sdk_never_breaks_local_logging(self):
        from scripts.observability import emit_event

        log_path = Path(self.tmp.name) / "events.jsonl"
        env = {
            "OBSERVABILITY_LOG_PATH": str(log_path),
            "SENTRY_DSN": "https://public@example.invalid/1",
            "LANGFUSE_PUBLIC_KEY": "pk-lf-test",
            "LANGFUSE_SECRET_KEY": "sk-lf-test-secret",
        }
        with patch.dict(sys.modules, {"sentry_sdk": None, "langfuse": None}):
            emit_event("worker.started", {"job_id": "job-1"}, env=env)

        self.assertTrue(log_path.exists())
        self.assertIn("worker.started", log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
