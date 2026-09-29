from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_WORKFLOWS = (
    ".github/workflows/ai-worker-gpt56.yml",
    ".github/workflows/desk-notify.yml",
    ".github/workflows/gemini-senses.yml",
)


class ActiveWorkflowActionsVersionTests(unittest.TestCase):
    def test_active_scheduled_workflows_use_checkout_v7(self) -> None:
        for relative in ACTIVE_WORKFLOWS:
            text = (ROOT / relative).read_text(encoding="utf-8")
            with self.subTest(workflow=relative):
                self.assertNotIn("actions/checkout@v4", text)
                self.assertIn("actions/checkout@v7", text)


if __name__ == "__main__":
    unittest.main()
