import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.work_queue import InvalidTransition, WorkQueue

UTC = timezone.utc


def item(job_id="job-1", **overrides):
    base = {
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
    base.update(overrides)
    return base


class WorkQueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "work_queue.json"
        self.path.write_text(json.dumps({"version": 1, "items": [item()]}), encoding="utf-8")
        self.queue = WorkQueue(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_legal_transition_queued_to_claimed_and_complete(self):
        now = datetime(2026, 9, 26, 3, 1, tzinfo=UTC)
        claimed = self.queue.claim("job-1", "grok", now=now)
        self.assertEqual(claimed["status"], "claimed")
        self.assertEqual(claimed["attempt_count"], 1)
        self.assertEqual(claimed["claim"]["worker"], "grok")

        completed = self.queue.complete("job-1", {"finding": "ok"}, worker="grok", now=now)
        self.assertEqual(completed["status"], "completed")
        self.assertEqual(completed["result"], {"finding": "ok"})

    def test_illegal_transition_is_rejected(self):
        with self.assertRaises(InvalidTransition):
            self.queue.complete("job-1", {"finding": "not claimed"}, worker="grok")

    def test_duplicate_completion_is_idempotent(self):
        now = datetime(2026, 9, 26, 3, 1, tzinfo=UTC)
        self.queue.claim("job-1", "grok", now=now)
        first = self.queue.complete("job-1", {"finding": "first"}, worker="grok", now=now)
        second = self.queue.complete("job-1", {"finding": "second"}, worker="grok", now=now)
        self.assertEqual(second, first)
        reloaded = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(reloaded["items"][0]["result"], {"finding": "first"})

    def test_expired_claim_can_be_reclaimed_without_concurrent_ownership(self):
        first = datetime(2026, 9, 26, 3, 0, tzinfo=UTC)
        self.queue.claim("job-1", "grok", now=first, lease_seconds=60)

        with self.assertRaises(InvalidTransition):
            self.queue.claim("job-1", "grok", now=first + timedelta(seconds=30), lease_seconds=60)

        reclaimed = self.queue.claim("job-1", "grok", now=first + timedelta(seconds=61), lease_seconds=60)
        self.assertEqual(reclaimed["status"], "claimed")
        self.assertEqual(reclaimed["claim"]["worker"], "grok")
        self.assertEqual(reclaimed["attempt_count"], 2)

    def test_retryable_failure_returns_job_to_retryable_state(self):
        now = datetime(2026, 9, 26, 3, 1, tzinfo=UTC)
        self.queue.claim("job-1", "grok", now=now)
        failed = self.queue.fail("job-1", "temporary provider error", retryable=True, worker="grok", now=now)
        self.assertEqual(failed["status"], "retryable_failed")
        self.assertEqual(failed["blocker"], "temporary provider error")

        retried = self.queue.claim("job-1", "grok", now=now + timedelta(seconds=1))
        self.assertEqual(retried["status"], "claimed")
        self.assertEqual(retried["attempt_count"], 2)

    def test_non_retryable_failure_is_blocked(self):
        now = datetime(2026, 9, 26, 3, 1, tzinfo=UTC)
        self.queue.claim("job-1", "grok", now=now)
        failed = self.queue.fail("job-1", "missing credentials", retryable=False, worker="grok", now=now)
        self.assertEqual(failed["status"], "blocked")
        with self.assertRaises(InvalidTransition):
            self.queue.claim("job-1", "grok", now=now + timedelta(seconds=1))

    def test_retry_exhaustion_enters_dead_letter(self):
        self.path.write_text(json.dumps({"version": 1, "items": [item(max_attempts=1)]}), encoding="utf-8")
        queue = WorkQueue(self.path)
        now = datetime(2026, 9, 26, 3, 1, tzinfo=UTC)
        queue.claim("job-1", "grok", now=now)
        failed = queue.fail("job-1", "temporary provider error", retryable=True, worker="grok", now=now)
        self.assertEqual(failed["status"], "dead_letter")


if __name__ == "__main__":
    unittest.main()
