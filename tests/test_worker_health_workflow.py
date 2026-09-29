from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ai-worker-gpt56.yml"


class WorkerHealthWorkflowTests(unittest.TestCase):
    def test_health_snapshot_receives_github_token(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        health_section = text.split("- name: Health snapshot", 1)[1].split("- name:", 1)[0]
        self.assertIn("GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}", health_section)


if __name__ == "__main__":
    unittest.main()
