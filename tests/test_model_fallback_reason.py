import unittest

from scripts.model_fallback import CannotDo, ModelFallback
from scripts.worker_adapters import NonRetryableProviderError


class _Bad:
    def run(self, job):
        raise NonRetryableProviderError("provider result missing required keys: ['evidence']")


class ModelFallbackReasonTest(unittest.TestCase):
    def test_error_reason_is_recorded_and_surfaced(self):
        fb = ModelFallback([("github_models", _Bad()), ("groq", None)])
        with self.assertRaises(CannotDo) as ctx:
            fb.run({"id": "j", "objective": "x"})
        msg = str(ctx.exception)
        self.assertTrue(msg.startswith("YAPAMADIM:"))
        self.assertIn("github_models=error", msg)
        self.assertIn("hata_nedeni: github_models: NonRetryableProviderError: provider result missing required keys", msg)
        self.assertEqual(fb.attempts[1], {"provider": "groq", "status": "no_key"})


if __name__ == "__main__":
    unittest.main()
