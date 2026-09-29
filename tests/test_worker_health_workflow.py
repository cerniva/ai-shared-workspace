from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from scripts import worker_health


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ai-worker-gpt56.yml"


class WorkerHealthWorkflowTests(unittest.TestCase):
    def test_health_snapshot_receives_github_token(self) -> None:
        text = WORKFLOW.read_text(encoding="utf-8")
        health_section = text.split("- name: Health snapshot", 1)[1].split("- name:", 1)[0]
        self.assertIn("GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}", health_section)

    def test_health_does_not_claim_provider_readiness_from_credentials(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            state = root / "state"
            state.mkdir()
            (state / "work_queue.json").write_text(json.dumps({"version": 1, "items": []}), encoding="utf-8")
            (state / "dead_letter.json").write_text(json.dumps({"version": 1, "items": []}), encoding="utf-8")
            env = {
                "OPENAI_API_KEY": "configured-not-validated",
                "GEMINI_API_KEY": "configured-not-validated",
                "XAI_API_KEY": "",
                "META_MODEL_API_KEY": "",
            }
            with patch.object(worker_health, "ROOT", root), patch.dict("os.environ", env, clear=True):
                result = worker_health.build_health(datetime(2026, 9, 29, tzinfo=timezone.utc))

        self.assertTrue(result["healthy"])
        self.assertEqual(result["health_scope"], "queue-and-dead-letter-structure-only")
        self.assertFalse(result["provider_readiness_checked"])
        self.assertFalse(result["model"]["readiness_checked"])
        self.assertEqual(result["routing"]["worker_failover_order"], ["gemini", "openai", "grok", "meta"])
        self.assertTrue(result["routing"]["configured_worker_providers"]["gemini"])
        self.assertTrue(result["routing"]["configured_worker_providers"]["openai"])


if __name__ == "__main__":
    unittest.main()
