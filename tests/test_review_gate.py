import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.review_gate import review_job
from scripts.work_queue import InvalidTransition, WorkQueue

UTC = timezone.utc


def completed_item(job_id="job-1"):
    return {
        "id": job_id,
        "project": "workspace",
        "objective": "research",
        "worker": "grok",
        "priority": 50,
        "created_at": "2026-09-26T03:00:00+00:00",
        "status": "completed",
        "evidence_requirements": [],
        "max_attempts": 3,
        "attempt_count": 1,
        "blocker": None,
        "claim": None,
        "result": {"recommendation": "ship", "confidence": 0.9},
    }


class ReviewGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.queue_path = Path(self.tmp.name) / "queue.json"
        self.lessons_path = Path(self.tmp.name) / "lessons.md"
        self.queue_path.write_text(json.dumps({"version": 1, "items": [completed_item()]}), encoding="utf-8")
        self.now = datetime(2026, 9, 26, 3, 10, tzinfo=UTC)

    def tearDown(self):
        self.tmp.cleanup()

    def test_unreviewed_completed_job_cannot_be_applied_directly(self):
        queue = WorkQueue(self.queue_path)
        with self.assertRaises(InvalidTransition):
            queue.mark_applied("job-1", now=self.now)

    def test_rejected_result_is_reviewed_but_not_applied_or_promoted(self):
        state = review_job(
            WorkQueue(self.queue_path),
            "job-1",
            verdict="reject",
            rationale="evidence too weak",
            action="none",
            metric="none",
            accepted_lessons=["Do not promote this"],
            lessons_path=self.lessons_path,
            now=self.now,
        )
        self.assertEqual(state["status"], "reviewed")
        self.assertEqual(state["review"]["verdict"], "reject")
        self.assertFalse(self.lessons_path.exists())

    def test_accepted_result_is_applied_and_promotes_lessons(self):
        state = review_job(
            WorkQueue(self.queue_path),
            "job-1",
            verdict="accept",
            rationale="evidence sufficient",
            action="test checkout",
            metric="conversion_rate",
            accepted_lessons=["Verify digital delivery before publishing."],
            lessons_path=self.lessons_path,
            now=self.now,
        )
        self.assertEqual(state["status"], "applied")
        text = self.lessons_path.read_text(encoding="utf-8")
        self.assertIn("Verify digital delivery before publishing.", text)
        self.assertIn("job-1", text)
        self.assertIn("conversion_rate", text)


if __name__ == "__main__":
    unittest.main()
