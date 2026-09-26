import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.worker_adapters import GeminiAdapter, GrokAdapter

JOB = {
    "id": "job-42",
    "project": "workspace",
    "objective": "Find one validated growth opportunity",
    "worker": "grok",
    "evidence_requirements": ["source URL"],
}


class LiveAdapterTransportTests(unittest.TestCase):
    def test_grok_uses_responses_endpoint_and_normalizes_output(self):
        calls = []

        def transport(url, headers, payload, timeout):
            calls.append((url, headers, payload, timeout))
            return {
                "model": "grok-4.7",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": '{"evidence": [], "factual_findings": ["fact"], "hypotheses": [], "recommendation": "act", "confidence": 0.8, "next_action": "review"}'}]}],
                "usage": {"input_tokens": 10, "output_tokens": 5},
            }

        result = GrokAdapter(api_key="secret", model="grok-4.7", transport=transport).run(JOB)
        self.assertEqual(calls[0][0], "https://api.x.ai/v1/responses")
        self.assertEqual(calls[0][1]["Authorization"], "Bearer secret")
        self.assertEqual(calls[0][2]["model"], "grok-4.7")
        self.assertEqual(result["factual_findings"], ["fact"])
        self.assertEqual(result["provider"], "grok")

    def test_gemini_uses_generate_content_and_normalizes_output(self):
        calls = []

        def transport(url, headers, payload, timeout):
            calls.append((url, headers, payload, timeout))
            return {
                "candidates": [{"content": {"parts": [{"text": '{"evidence": [], "factual_findings": ["fact"], "hypotheses": [], "recommendation": "act", "confidence": 0.7, "next_action": "review"}'}]}}],
                "usageMetadata": {"promptTokenCount": 11, "candidatesTokenCount": 4},
            }

        result = GeminiAdapter(api_key="secret", model="gemini-3.6-flash", transport=transport).run(JOB)
        self.assertEqual(calls[0][0], "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent")
        self.assertEqual(calls[0][1]["x-goog-api-key"], "secret")
        self.assertEqual(result["factual_findings"], ["fact"])
        self.assertEqual(result["provider"], "gemini")


if __name__ == "__main__":
    unittest.main()
