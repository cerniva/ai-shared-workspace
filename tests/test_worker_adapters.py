import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.worker_adapters import (
    GeminiAdapter,
    GrokAdapter,
    MissingCredential,
    MockAdapter,
)


JOB = {
    "id": "job-1",
    "project": "workspace",
    "objective": "Find current revenue opportunities",
    "worker": "grok",
    "evidence_requirements": ["source URLs"],
}


class WorkerAdapterTests(unittest.TestCase):
    def test_mock_adapter_returns_normalized_result(self):
        result = MockAdapter(provider="grok", model="mock-grok").run(JOB)
        self.assertEqual(result["provider"], "grok")
        self.assertEqual(result["model"], "mock-grok")
        self.assertEqual(result["job_id"], "job-1")
        self.assertIsInstance(result["evidence"], list)
        self.assertIsInstance(result["factual_findings"], list)
        self.assertIsInstance(result["hypotheses"], list)
        self.assertIsInstance(result["recommendation"], str)
        self.assertIsInstance(result["confidence"], float)
        self.assertIsInstance(result["next_action"], str)
        self.assertIn("timing", result)
        self.assertIn("usage", result)

    def test_grok_missing_secret_blocks_before_request(self):
        adapter = GrokAdapter(api_key="", model="grok-test")
        with self.assertRaises(MissingCredential):
            adapter.run(JOB)
        self.assertEqual(adapter.request_count, 0)

    def test_gemini_missing_secret_blocks_before_request(self):
        adapter = GeminiAdapter(api_key=None, model="gemini-test")
        with self.assertRaises(MissingCredential):
            adapter.run(JOB)
        self.assertEqual(adapter.request_count, 0)


if __name__ == "__main__":
    unittest.main()
