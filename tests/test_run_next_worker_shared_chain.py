import unittest
from pathlib import Path

from scripts.model_fallback import ModelFallback
from scripts.run_next_worker import make_worker_adapter

ROOT = Path(__file__).resolve().parents[1]


class SharedChainTests(unittest.TestCase):
    def test_github_token_alone_gives_shared_chain_with_github_models(self):
        adapter = make_worker_adapter(env={"GITHUB_TOKEN": "t"})
        self.assertIsInstance(adapter, ModelFallback)
        live = [name for name, a in adapter.entries if a is not None]
        self.assertIn("github_models", live)

    def test_workflow_grants_models_read_and_shared_secrets(self):
        text = (ROOT / ".github" / "workflows" / "ai-worker-gpt56.yml").read_text(encoding="utf-8")
        self.assertIn("models: read", text)
        for key in ("GITHUB_TOKEN", "GROQ_API_KEY", "OPENROUTER_API_KEY", "CEREBRAS_API_KEY", "MISTRAL_API_KEY"):
            self.assertIn(f"{key}: ${{{{ secrets.{key} }}}}", text)

    def test_run_next_worker_uses_shared_adapter(self):
        src = (ROOT / "scripts" / "run_next_worker.py").read_text(encoding="utf-8")
        self.assertIn("make_worker_adapter(),", src)


if __name__ == "__main__":
    unittest.main()
