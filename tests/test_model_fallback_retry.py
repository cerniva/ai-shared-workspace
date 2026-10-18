import unittest

from scripts.model_fallback import ModelFallback
from scripts.worker_adapters import RetryableProviderError


class _Flaky:
    def __init__(self, fails, exc=None):
        self.fails = fails
        self.calls = 0
        self.exc = exc or RetryableProviderError("provider returned non-JSON body")

    def run(self, job):
        self.calls += 1
        if self.calls <= self.fails:
            raise self.exc
        return {"recommendation": "ok"}


class ModelFallbackRetryTest(unittest.TestCase):
    def test_transient_error_retried_once_on_same_provider(self):
        a = _Flaky(1)
        slept = []
        fb = ModelFallback([("github_models", a)], sleeper=slept.append)
        self.assertEqual(fb.run({"id": "j"}), {"recommendation": "ok"})
        self.assertEqual(a.calls, 2)
        self.assertEqual(len(slept), 1)
        self.assertEqual(fb.attempts, [{"provider": "github_models", "status": "ok"}])

    def test_second_transient_failure_falls_through_with_reason(self):
        a, b = _Flaky(5), _Flaky(0)
        fb = ModelFallback([("github_models", a), ("groq", b)], sleeper=lambda s: None)
        self.assertEqual(fb.run({"id": "j"}), {"recommendation": "ok"})
        self.assertEqual(a.calls, 2)
        self.assertEqual(fb.attempts[0]["status"], "error")
        self.assertIn("non-JSON body", fb.attempts[0]["reason"])

    def test_quota_is_not_retried(self):
        a = _Flaky(5, RetryableProviderError("provider HTTP 429 host=x"))
        fb = ModelFallback([("gemini", a), ("groq", _Flaky(0))], sleeper=lambda s: None)
        fb.run({"id": "j"})
        self.assertEqual(a.calls, 1)
        self.assertEqual(fb.attempts[0]["status"], "quota")


if __name__ == "__main__":
    unittest.main()
