import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.review_gate import review_job
from scripts.run_worker import execute
from scripts.work_queue import WorkQueue


class EndToEndWorkerFlowTests(unittest.TestCase):
    def test_queue_worker_review_lesson_flow(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            queue_path = root / "queue.json"
            dead_path = root / "dead.json"
            lessons_path = root / "lessons.md"
            queue_path.write_text(json.dumps({"version": 1, "items": [{
                "id": "job-e2e", "project": "workspace", "objective": "research",
                "worker": "grok", "priority": 50,
                "created_at": "2026-09-26T03:00:00+00:00", "status": "queued",
                "evidence_requirements": [], "max_attempts": 2, "attempt_count": 0,
                "blocker": None, "claim": None, "result": None
            }]}), encoding="utf-8")

            completed = execute([
                "--job", "job-e2e", "--provider", "grok",
                "--queue", str(queue_path), "--dead-letter", str(dead_path), "--mock"
            ], env={})
            self.assertEqual(completed["status"], "completed")

            applied = review_job(
                WorkQueue(queue_path), "job-e2e", verdict="accept",
                rationale="mock integration verified", action="measure",
                metric="conversion", accepted_lessons=["Mock flow verified."],
                lessons_path=lessons_path,
            )
            self.assertEqual(applied["status"], "applied")
            self.assertIn("Mock flow verified.", lessons_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
