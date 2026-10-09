from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts import ai_roster_check, handoff
from scripts.provider_config import (
    FAILOVER_ORDER, PROVIDER_ENV, PROVIDER_ROLES, FailoverAdapter, credential_status,
    make_adapter, make_failover_adapter, providers_for_role,
)
from scripts.frontier_adapters import ClaudeAdapter, DeepSeekAdapter, PerplexityAdapter
from scripts.worker_adapters import GeminiAdapter, MissingCredential, ProviderAuthError, RetryableProviderError

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = {"evidence": [], "factual_findings": ["f"], "hypotheses": [], "recommendation": "ok",
           "confidence": 0.9, "next_action": "none"}
JOB = {"id": "j1", "objective": "test"}


class Recorder:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def __call__(self, url, headers, payload, timeout):
        self.calls.append((url, headers, payload))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class AdapterTests(unittest.TestCase):
    def test_claude_messages_api(self):
        t = Recorder({"model": "claude-sonnet-5-5", "content": [{"type": "text", "text": json.dumps(PAYLOAD)}],
                      "usage": {"input_tokens": 1}})
        out = ClaudeAdapter("k", transport=t, workspace_id="ws").run(JOB)
        url, headers, body = t.calls[0]
        self.assertEqual(url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(headers["x-api-key"], "k")
        self.assertEqual(headers["anthropic-version"], "2023-06-01")
        self.assertEqual(headers["anthropic-workspace-id"], "ws")
        self.assertIn("max_tokens", body)
        self.assertEqual(body["messages"][0]["role"], "user")
        self.assertEqual(out["provider"], "claude")
        self.assertEqual(out["recommendation"], "ok")

    def test_perplexity_keeps_citations(self):
        t = Recorder({"model": "sonar", "choices": [{"message": {"content": json.dumps(PAYLOAD)}}],
                      "citations": ["https://a.example/1", "https://b.example/2"],
                      "search_results": [{"title": "A", "url": "https://a.example/1", "date": "2026-10-01"}]})
        out = PerplexityAdapter("k", "sonar", transport=t).run(JOB)
        url, headers, body = t.calls[0]
        self.assertEqual(url, "https://api.perplexity.ai/v1/sonar")
        self.assertEqual(headers["Authorization"], "Bearer k")
        self.assertEqual([c["url"] for c in out["citations"]], ["https://a.example/1", "https://b.example/2"])
        self.assertEqual(out["citations"][0]["title"], "A")
        self.assertEqual(sum(1 for e in out["evidence"] if e.get("type") == "citation"), 2)

    def test_deepseek_openai_compatible(self):
        t = Recorder({"model": "deepseek-flash", "choices": [{"message": {"content": json.dumps(PAYLOAD)}}]})
        out = DeepSeekAdapter("k", "deepseek-flash", transport=t).run(JOB)
        url, headers, body = t.calls[0]
        self.assertEqual(url, "https://api.deepseek.com/chat/completions")
        self.assertEqual(headers["Authorization"], "Bearer k")
        self.assertFalse(body["stream"])
        self.assertEqual(out["provider"], "deepseek")

    def test_gemini_endpoint(self):
        t = Recorder({"candidates": [{"content": {"parts": [{"text": json.dumps(PAYLOAD)}]}}]})
        GeminiAdapter("k", "gemini-3.6-flash", transport=t).run(JOB)
        self.assertTrue(t.calls[0][0].startswith("https://generativelanguage.googleapis.com/v1beta/models/"))

    def test_missing_key_raises_missing_credential(self):
        for cls in (ClaudeAdapter, PerplexityAdapter, DeepSeekAdapter):
            with self.subTest(cls=cls.__name__), self.assertRaises(MissingCredential):
                cls("", "m", transport=Recorder({})).run(JOB)
        for name in ("claude", "perplexity", "deepseek", "gemini"):
            with self.subTest(name=name), self.assertRaises(MissingCredential):
                make_adapter(name, env={})


class ConfigTests(unittest.TestCase):
    def test_roles(self):
        self.assertEqual(PROVIDER_ROLES["perplexity"], "research_with_citations")
        self.assertEqual(PROVIDER_ROLES["claude"], "code_review_long_text")
        self.assertEqual(PROVIDER_ROLES["deepseek"], "cheap_analysis_and_code")
        self.assertEqual(PROVIDER_ROLES["gemini"], "second_opinion")
        self.assertEqual(providers_for_role("research_with_citations"), ["perplexity"])
        self.assertEqual(set(FAILOVER_ORDER), set(PROVIDER_ENV))

    def test_env_names(self):
        self.assertEqual(PROVIDER_ENV["claude"], "ANTHROPIC_API_KEY")
        self.assertEqual(PROVIDER_ENV["perplexity"], "PERPLEXITY_API_KEY")
        self.assertEqual(PROVIDER_ENV["deepseek"], "DEEPSEEK_API_KEY")
        self.assertEqual(PROVIDER_ENV["gemini"], "GEMINI_API_KEY")

    def test_failover_includes_only_configured_new_providers(self):
        fa = make_failover_adapter(env={"DEEPSEEK_API_KEY": "d", "PERPLEXITY_API_KEY": " "})
        self.assertEqual([a.provider for a in fa.adapters], ["deepseek"])
        with self.assertRaises(MissingCredential):
            make_failover_adapter(env={})

    def test_failover_skips_auth_and_missing(self):
        good = DeepSeekAdapter("k", "m", transport=Recorder(
            {"choices": [{"message": {"content": json.dumps(PAYLOAD)}}]}))
        bad = ClaudeAdapter("k", transport=Recorder(ProviderAuthError("x", http_status=401, endpoint_host="h")))
        missing = PerplexityAdapter("", "sonar")
        out = FailoverAdapter([missing, bad, good]).run(JOB)
        self.assertEqual(out["provider"], "deepseek")

    def test_credential_status_names_only(self):
        st = credential_status(env={"ANTHROPIC_API_KEY": "secret-value"})
        self.assertEqual(st["claude"]["status"], "configured")
        self.assertEqual(st["perplexity"]["status"], "missing")
        self.assertNotIn("secret-value", json.dumps(st))


class RosterTests(unittest.TestCase):
    def test_roster_never_crashes_and_no_values(self):
        def factory(name, env=None):
            if name == "claude":
                return ClaudeAdapter("k", transport=Recorder(RetryableProviderError("provider HTTP 529 host=h")))
            if name == "deepseek":
                raise RuntimeError("boom")
            return make_adapter(name, env=env)
        env = {"ANTHROPIC_API_KEY": "secret-a", "DEEPSEEK_API_KEY": "secret-d"}
        rep = ai_roster_check.check(env=env, factory=factory)
        self.assertEqual(rep["providers"]["claude"]["test_call"], "error")
        self.assertEqual(rep["providers"]["deepseek"]["test_call"], "error")
        self.assertEqual(rep["providers"]["perplexity"]["test_call"], "skipped_missing_credential")
        self.assertIn("PERPLEXITY_API_KEY", rep["missing_secrets"])
        self.assertNotIn("secret-", json.dumps(rep))

    def test_dry_run_cli(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "r.json"
            self.assertEqual(ai_roster_check.main(["--out", str(out), "--dry-run"]), 0)
            self.assertEqual(set(json.loads(out.read_text())["providers"]), set(PROVIDER_ENV))


class TeamWiringTests(unittest.TestCase):
    def test_handoff_actors(self):
        for actor in ("gemini", "claude", "perplexity", "deepseek", "grok", "chatgpt"):
            self.assertIn(actor, handoff.ACTORS)
        data = {"schema_version": 1, "items": []}
        handoff.add(data, item_id="T1", sender="grok", receiver="perplexity", task="t", reason="r", evidence="e")
        handoff.transition(data, "T1", "claim", actor="perplexity")

    def test_channels_and_inboxes(self):
        from scripts import desk_bridge
        for name in ("claude", "perplexity", "deepseek"):
            self.assertIn(f"inbox-{name}", desk_bridge.CHANNELS)
            self.assertTrue((ROOT / "messages" / f"inbox-{name}.md").exists())

    def test_workflow(self):
        text = (ROOT / ".github/workflows/ai-roster-check.yml").read_text()
        self.assertIn("workflow_dispatch", text)
        for env_name in PROVIDER_ENV.values():
            self.assertIn(f"secrets.{env_name}", text)


if __name__ == "__main__":
    unittest.main()
