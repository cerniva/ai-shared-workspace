"""Regression: exhausted model fallback must not be blindly retried.

These tests exercise the real WorkQueue transitions with no network calls,
credentials, paid providers or changes to main.
"""
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts.model_fallback import CannotDo
from scripts.work_queue import WorkQueue
from scripts.worker_runner import run_job


class FailingFallback:
    def __init__(self, statuses):
        self.attempts = [{"provider": "mock", "status": status} for status in statuses]

    def run(self, job):
        raise CannotDo("YAPAMADIM: simulated provider chain exhausted")


class CannotDoQueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.queue_path = Path(self.temp.name) / "queue.json"
        self.dead_path = Path(self.temp.name) / "dead.json"
        self.now = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)

    def run_case(self, statuses, *, max_attempts=3):
        item = {
            "id": "fallback-job", "project": "workspace",
            "objective": "Mock provider failure classification", "worker": "chatgpt",
            "priority": 1, "created_at": "2026-10-18T23:00:00+00:00",
            "status": "queued", "evidence_requirements": [],
            "max_attempts": max_attempts, "attempt_count": 0,
            "blocker": None, "claim": None, "result": None,
        }
        self.queue_path.write_text(json.dumps({"version": 1, "items": [item]}), encoding="utf-8")
        return run_job(
            WorkQueue(self.queue_path), "fallback-job", FailingFallback(statuses),
            worker="chatgpt", dead_letter_path=self.dead_path, now=self.now,
        )

    def test_auth_with_transient_error_is_terminal(self):
        state = self.run_case(["auth", "error"])
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["attempt_count"], 1)
        self.assertFalse(self.dead_path.exists())

    def test_billing_with_quota_is_terminal(self):
        self.assertEqual(self.run_case(["billing", "quota"])["status"], "blocked")

    def test_all_missing_keys_is_terminal(self):
        self.assertEqual(self.run_case(["no_key"])["status"], "blocked")

    def test_unclassified_failure_without_attempts_is_terminal(self):
        self.assertEqual(self.run_case([])["status"], "blocked")

    def test_only_transient_gateway_error_is_retryable(self):
        self.assertEqual(self.run_case(["error"])["status"], "retryable_failed")

    def test_only_quota_is_bounded_retryable(self):
        self.assertEqual(self.run_case(["quota"])["status"], "retryable_failed")

    def test_retry_budget_exhaustion_records_dead_letter(self):
        state = self.run_case(["error"], max_attempts=1)
        self.assertEqual(state["status"], "dead_letter")
        self.assertEqual(len(json.loads(self.dead_path.read_text(encoding="utf-8"))["items"]), 1)


if __name__ == "__main__":
    unittest.main()
