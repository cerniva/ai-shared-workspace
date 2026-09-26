import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_worker import execute


def item(job_id="job-1"):
    return {
        "id": job_id,
        "project": "workspace",
        "objective": "research",
        "worker": "grok",
        "priority": 50,
        "created_at": "2026-09-26T03:00:00+00:00",
        "status": "queued",
        "evidence_requirements": [],
        "max_attempts": 3,
        "attempt_count": 0,
        "blocker": None,
        "claim": None,
        "result": None,
    }


class RunWorkerTests(unittest.TestCase):
    def test_mock_entrypoint_runs_queue_job_without_credentials(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue_path = Path(tmp) / "queue.json"
            dead_path = Path(tmp) / "dead.json"
            queue_path.write_text(json.dumps({"version": 1, "items": [item()]}), encoding="utf-8")
            state = execute(
                [
                    "--job", "job-1",
                    "--provider", "grok",
                    "--queue", str(queue_path),
                    "--dead-letter", str(dead_path),
                    "--mock",
                ],
                env={},
            )
            self.assertEqual(state["status"], "completed")
            self.assertEqual(state["result"]["provider"], "grok")


if __name__ == "__main__":
    unittest.main()
