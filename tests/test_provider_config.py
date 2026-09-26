import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.provider_config import ConfigError, make_adapter
from scripts.worker_adapters import GeminiAdapter, GrokAdapter, MissingCredential


class ProviderConfigTests(unittest.TestCase):
    def test_grok_requires_api_key(self):
        with self.assertRaises(MissingCredential):
            make_adapter("grok", env={})

    def test_gemini_requires_api_key(self):
        with self.assertRaises(MissingCredential):
            make_adapter("gemini", env={})

    def test_unknown_provider_is_rejected(self):
        with self.assertRaises(ConfigError):
            make_adapter("unknown", env={})

    def test_grok_builds_from_environment(self):
        adapter = make_adapter("grok", env={"XAI_API_KEY": "secret", "XAI_MODEL": "grok-current"})
        self.assertIsInstance(adapter, GrokAdapter)
        self.assertEqual(adapter.model, "grok-current")

    def test_gemini_builds_from_environment(self):
        adapter = make_adapter("gemini", env={"GEMINI_API_KEY": "secret", "GEMINI_MODEL": "gemini-current"})
        self.assertIsInstance(adapter, GeminiAdapter)
        self.assertEqual(adapter.model, "gemini-current")


if __name__ == "__main__":
    unittest.main()
