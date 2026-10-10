from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import model_fallback as mf
from scripts import provider_health as ph
from scripts.worker_adapters import RetryableProviderError, NonRetryableProviderError, ProviderAuthError

SECRET = "tok-SECRETVALUE-123456"
JOB = {"id": "j1", "project": "workspace", "objective": "x"}
GOOD = {"choices": [{"message": {"content": json.dumps({
    "evidence": [], "factual_findings": ["f"], "hypotheses": [], "recommendation": "r",
    "confidence": 0.5, "next_action": "n"})}}], "model": "m"}


class ProviderHealthTests(unittest.TestCase):
    def test_no_key_reported_for_every_provider(self):
        rep = ph.check(env={}, http=lambda *a: self.fail("no call without key"))
        names = [r["name"] for r in rep["providers"]]
        self.assertEqual(names[:5], ["github_models", "groq", "openrouter_free", "cerebras", "mistral"])
        self.assertEqual(names[-1], "local")
        self.assertTrue(all(r["status"] == "no_key" for r in rep["providers"]))
        self.assertEqual(rep["usable"], [])

    def test_status_mapping_and_no_secret(self):
        codes = {"models.github.ai": (403, ""), "groq.com": (429, "rate"), "openrouter.ai": (402, ""),
                 "cerebras.ai": (200, ""), "mistral.ai": (400, "insufficient credit balance"),
                 "googleapis": (401, ""), "deepseek": (500, "")}
        seen = []

        def http(url, headers, payload, timeout):
            seen.append(payload)
            if payload and "max_tokens" in payload:
                self.assertEqual(payload["max_tokens"], 1)
            for k, v in codes.items():
                if k in url:
                    return v
            raise OSError("down")
        env = {k: SECRET for k in ("GITHUB_TOKEN", "GROQ_API_KEY", "OPENROUTER_API_KEY", "CEREBRAS_API_KEY",
                                   "MISTRAL_API_KEY", "GEMINI_API_KEY", "DEEPSEEK_API_KEY", "OPENAI_API_KEY")}
        rep = ph.check(env=env, http=http)
        st = {r["name"]: r["status"] for r in rep["providers"]}
        self.assertEqual(st["github_models"], "auth")
        self.assertEqual(st["groq"], "quota")
        self.assertEqual(st["openrouter_free"], "billing")
        self.assertEqual(st["cerebras"], "ok")
        self.assertEqual(st["mistral"], "billing")
        self.assertEqual(st["gemini"], "auth")
        self.assertEqual(st["deepseek"], "error")
        self.assertEqual(st["openai"], "error")
        self.assertEqual(st["claude"], "no_key")
        self.assertTrue(seen[2]["model"].endswith(":free"))
        self.assertNotIn(SECRET, json.dumps(rep))
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "h.json"
            p.write_text(json.dumps(rep))
            self.assertIn("cerebras", ph.summary_lines(p)[1])
            md = Path(d) / "r.md"
            md.write_text("# r\n")
            orig = ph.HEALTH_PATH
            ph.HEALTH_PATH = p
            try:
                ph.summary_lines.__defaults__ = (p,)
                self.assertEqual(ph.main(["--append-report", str(md)]), 0)
            finally:
                ph.summary_lines.__defaults__ = (orig,)
                ph.HEALTH_PATH = orig
            self.assertIn("kullanilabilir: cerebras", md.read_text())


class FallbackTests(unittest.TestCase):
    def _env(self, *names):
        return {n: SECRET for n in names}

    def _chain(self, env, transport, tmp):
        return mf.fallback_adapter(env=env, transport=transport, health_path=Path(tmp) / "none.json")

    def test_429_goes_to_next_provider(self):
        calls = []

        def t(url, headers, payload, timeout):
            calls.append(url)
            if "groq" in url:
                raise RetryableProviderError("provider HTTP 429 host=api.groq.com")
            return GOOD
        with tempfile.TemporaryDirectory() as d:
            fa = self._chain(self._env("GROQ_API_KEY", "CEREBRAS_API_KEY"), t, d)
            res = fa.run(JOB)
        self.assertEqual(res["provider"], "cerebras")
        st = {a["provider"]: a["status"] for a in fa.attempts}
        self.assertEqual(st["groq"], "quota")
        self.assertEqual(st["github_models"], "no_key")
        self.assertEqual(st["openrouter_free"], "no_key")

    def test_402_billing_and_all_fail_yapamadim(self):
        def t(url, headers, payload, timeout):
            if "openrouter" in url:
                raise NonRetryableProviderError("provider HTTP 402 host=openrouter.ai")
            raise ProviderAuthError("provider HTTP 401 host=x", http_status=401, endpoint_host="x")
        with tempfile.TemporaryDirectory() as d:
            fa = self._chain(self._env("OPENROUTER_API_KEY", "MISTRAL_API_KEY"), t, d)
            with self.assertRaises(mf.CannotDo) as cm:
                fa.run(JOB)
        msg = str(cm.exception)
        self.assertTrue(msg.startswith("YAPAMADIM:"))
        self.assertIn("openrouter_free=billing", msg)
        self.assertIn("mistral=auth", msg)
        self.assertNotIn(SECRET, msg)

    def test_local_only_for_simple_jobs(self):
        with tempfile.TemporaryDirectory() as d:
            fa = self._chain({"OLLAMA_HOST": "http://localhost:11434"}, lambda *a: GOOD, d)
            with self.assertRaises(mf.CannotDo):
                fa.run(JOB)
            self.assertEqual(fa.run({**JOB, "simple": True})["provider"], "local")

    def test_none_without_any_key_and_health_demotion(self):
        self.assertIsNone(mf.fallback_adapter(env={}))
        with tempfile.TemporaryDirectory() as d:
            hp = Path(d) / "h.json"
            hp.write_text(json.dumps({"ts": datetime.now(timezone.utc).isoformat(),
                                      "providers": [{"name": "groq", "status": "billing"}]}))
            fa = mf.fallback_adapter(env=self._env("GROQ_API_KEY", "MISTRAL_API_KEY"), health_path=hp)
            self.assertEqual([a.provider for a in fa.adapters], ["mistral", "groq"])


if __name__ == "__main__":
    unittest.main()
