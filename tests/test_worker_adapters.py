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
    MetaAdapter,
    OpenAIAdapter,
    NonRetryableProviderError,
    _parse_json_text,
    _validate_strict_result,
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

    def test_openai_missing_secret_blocks_before_request(self):
        adapter = OpenAIAdapter(api_key="", model="gpt-5.6-sol")
        with self.assertRaises(MissingCredential):
            adapter.run(JOB)
        self.assertEqual(adapter.request_count, 0)

    def test_openai_adapter_parses_responses_output(self):
        import json
        def transport(url, headers, payload, timeout):
            self.assertEqual(url, "https://api.openai.com/v1/responses")
            self.assertEqual(payload["model"], "gpt-5.6-sol")
            return {"model": "gpt-5.6-sol", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(VALID_PAYLOAD)}]}], "usage": {"input_tokens": 10, "output_tokens": 5}}
        result = OpenAIAdapter(api_key="test-key", model="gpt-5.6-sol", transport=transport).run(JOB)
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["model"], "gpt-5.6-sol")

    def test_grok_missing_secret_blocks_before_request(self):
        adapter = GrokAdapter(api_key="", model="grok-test")
        with self.assertRaises(MissingCredential):
            adapter.run(JOB)
        self.assertEqual(adapter.request_count, 0)

    def test_meta_missing_secret_blocks_before_request(self):
        adapter = MetaAdapter(api_key="", model="muse-spark-1.3")
        with self.assertRaises(MissingCredential):
            adapter.run(JOB)
        self.assertEqual(adapter.request_count, 0)

    def test_meta_adapter_parses_responses_output(self):
        import json
        def transport(url, headers, payload, timeout):
            self.assertEqual(url, "https://api.meta.ai/v1/responses")
            self.assertEqual(payload["model"], "muse-spark-1.3")
            self.assertEqual(headers["Authorization"], "Bearer test-key")
            return {"model": "muse-spark-1.3", "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(VALID_PAYLOAD)}]}], "usage": {"input_tokens": 10}}
        result = MetaAdapter(api_key="test-key", model="muse-spark-1.3", transport=transport).run(JOB)
        self.assertEqual(result["provider"], "meta")
        self.assertEqual(result["job_id"], "job-1")

    def test_gemini_missing_secret_blocks_before_request(self):
        adapter = GeminiAdapter(api_key=None, model="gemini-test")
        with self.assertRaises(MissingCredential):
            adapter.run(JOB)
        self.assertEqual(adapter.request_count, 0)


VALID_PAYLOAD = {
    "evidence": [{"type": "url", "value": "https://example.com"}],
    "factual_findings": ["fact one"],
    "hypotheses": ["maybe"],
    "recommendation": "ship carefully",
    "confidence": 0.7,
    "next_action": "chatgpt_review",
}


class StrictJsonContractTests(unittest.TestCase):
    def test_valid_payload_passes(self):
        out = _validate_strict_result(dict(VALID_PAYLOAD))
        self.assertEqual(out["confidence"], 0.7)

    def test_missing_key_is_non_retryable(self):
        payload = dict(VALID_PAYLOAD)
        del payload["next_action"]
        with self.assertRaises(NonRetryableProviderError) as ctx:
            _validate_strict_result(payload)
        self.assertIn("missing required keys", str(ctx.exception))
        self.assertIn("next_action", str(ctx.exception))

    def test_extra_key_is_non_retryable(self):
        payload = dict(VALID_PAYLOAD)
        payload["surprise"] = True
        with self.assertRaises(NonRetryableProviderError) as ctx:
            _validate_strict_result(payload)
        self.assertIn("unexpected keys", str(ctx.exception))

    def test_wrong_type_is_non_retryable(self):
        payload = dict(VALID_PAYLOAD)
        payload["evidence"] = "not-a-list"
        with self.assertRaises(NonRetryableProviderError) as ctx:
            _validate_strict_result(payload)
        self.assertIn("evidence must be a list", str(ctx.exception))

    def test_confidence_bool_rejected(self):
        payload = dict(VALID_PAYLOAD)
        payload["confidence"] = True
        with self.assertRaises(NonRetryableProviderError):
            _validate_strict_result(payload)

    def test_parse_json_text_enforces_contract(self):
        import json
        with self.assertRaises(NonRetryableProviderError):
            _parse_json_text(json.dumps({"recommendation": "only"}))
        ok = _parse_json_text(json.dumps(VALID_PAYLOAD))
        self.assertEqual(ok["next_action"], "chatgpt_review")

    def test_grok_adapter_rejects_loose_json(self):
        def transport(url, headers, payload, timeout):
            return {
                "model": "grok-test",
                "output": [{
                    "type": "message",
                    "content": [{"type": "output_text", "text": '{"recommendation": "loose"}'}],
                }],
                "usage": {},
            }

        adapter = GrokAdapter(api_key="test-key", model="grok-test", transport=transport)
        with self.assertRaises(NonRetryableProviderError):
            adapter.run(JOB)


if __name__ == "__main__":
    unittest.main()
