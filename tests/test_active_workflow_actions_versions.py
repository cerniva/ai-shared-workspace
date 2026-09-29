from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_WORKFLOWS = (
    ".github/workflows/ai-worker-gpt56.yml",
    ".github/workflows/desk-notify.yml",
    ".github/workflows/gemini-senses.yml",
    ".github/workflows/codeql.yml",
    ".github/workflows/worker-orchestration-tests.yml",
    ".github/workflows/shorts-render-tests.yml",
    ".github/workflows/shorts-free-smoke-once.yml",
    ".github/workflows/youtube-upload.yml",
    ".github/workflows/meta-senses.yml",
    ".github/workflows/grok-file-desk.yml",
    ".github/workflows/tinyfish-senses.yml",
    ".github/workflows/meta-bridge-auto.yml",
    ".github/workflows/firecrawl-fallback.yml",
    ".github/workflows/claude-api-diagnostic.yml",
    ".github/workflows/tinyfish-event-bridge.yml",
    ".github/workflows/meta-ingest.yml",
    ".github/workflows/shorts-free-render.yml",
    ".github/workflows/browser-worker.yml",
    ".github/workflows/shorts-free-build.yml",
    ".github/workflows/web-worker-tests.yml",
)


class ActiveWorkflowActionsVersionTests(unittest.TestCase):
    def test_active_workflows_use_checkout_v7(self) -> None:
        for relative in ACTIVE_WORKFLOWS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(workflow=relative):
                self.assertNotIn("actions/checkout@v4", text)
                self.assertIn("actions/checkout@v7", text)


if __name__ == "__main__":
    unittest.main()
