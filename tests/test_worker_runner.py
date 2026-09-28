import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.work_queue import WorkQueue
from scripts.worker_adapters import MockAdapter, RetryableProviderError
from scripts.worker_runner import run_job

UTC = timezone.utc


def item(job_id, worker="grok", max_attempts=3):
    return {
        "id": job_id,
        "project": "workspace",
        "objective": f"objective {job_id}",
        "worker": worker,
        "priority": 50,
        "created_at": "2026-09-26T03:00:00+00:00",
        "status": "queued",
        "evidence_requirements": [],
        "max_attempts": max_attempts,
        "attempt_count": 0,
        "blocker": None,
        "claim": None,
        "result": None,
    }


class AlwaysRetryable:
    def run(self, job):
        raise RetryableProviderError("temporary outage")


class SecretRetryable:
    def run(self, job):
        secret_like = "sk-" + ("a" * 30)
        raise RetryableProviderError(f"temporary outage {secret_like}")


class WorkerRunnerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.queue_path = Path(self.tmp.name) / "queue.json"
        self.dead_path = Path(self.tmp.name) / "dead_letter.json"
        self.now = datetime(2026, 9, 26, 3, 5, tzinfo=UTC)

    def tearDown(self):
        self.tmp.cleanup()

    def write_items(self, items):
        self.queue_path.write_text(json.dumps({"version": 1, "items": items}), encoding="utf-8")

    def read_observability_events(self, path):
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def test_successful_mock_run_completes_job(self):
        self.write_items([item("job-1")])
        state = run_job(
            WorkQueue(self.queue_path),
            "job-1",
            MockAdapter(provider="grok", model="mock"),
            worker="grok",
            dead_letter_path=self.dead_path,
            now=self.now,
        )
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["result"]["provider"], "grok")

    def test_successful_run_records_started_and_completed_observability_events(self):
        self.write_items([item("job-1")])
        log_path = Path(self.tmp.name) / "observability.jsonl"
        with patch.dict(os.environ, {"OBSERVABILITY_LOG_PATH": str(log_path)}):
            state = run_job(
                WorkQueue(self.queue_path),
                "job-1",
                MockAdapter(provider="grok", model="mock"),
                worker="grok",
                dead_letter_path=self.dead_path,
                now=self.now,
            )

        self.assertEqual(state["status"], "completed")
        self.assertTrue(log_path.exists())
        events = self.read_observability_events(log_path)
        self.assertEqual([event["event"] for event in events], ["worker.started", "worker.completed"])
        self.assertEqual(events[0]["job_id"], "job-1")
        self.assertEqual(events[0]["worker"], "grok")
        completed = events[1]
        self.assertEqual(completed["provider"], "grok")
        self.assertEqual(completed["model"], "mock")
        self.assertIsInstance(completed["duration_ms"], int)
        self.assertEqual(
            completed["usage"],
            {"input_tokens": 0, "output_tokens": 0, "cost": 0},
        )

    def test_retryable_failure_returns_retryable_failed(self):
        self.write_items([item("job-1", max_attempts=2)])
        state = run_job(
            WorkQueue(self.queue_path),
            "job-1",
            AlwaysRetryable(),
            worker="grok",
            dead_letter_path=self.dead_path,
            now=self.now,
        )
        self.assertEqual(state["status"], "retryable_failed")
        self.assertEqual(state["attempt_count"], 1)

    def test_retryable_failure_observability_redacts_secret_like_text(self):
        self.write_items([item("job-1", max_attempts=2)])
        log_path = Path(self.tmp.name) / "observability.jsonl"
        secret_like = "sk-" + ("a" * 30)
        with patch.dict(os.environ, {"OBSERVABILITY_LOG_PATH": str(log_path)}):
            state = run_job(
                WorkQueue(self.queue_path),
                "job-1",
                SecretRetryable(),
                worker="grok",
                dead_letter_path=self.dead_path,
                now=self.now,
            )

        self.assertEqual(state["status"], "retryable_failed")
        raw = log_path.read_text(encoding="utf-8")
        self.assertNotIn(secret_like, raw)
        events = self.read_observability_events(log_path)
        self.assertEqual([event["event"] for event in events], ["worker.started", "worker.retryable_failed"])
        self.assertEqual(events[-1]["error"], "temporary outage [REDACTED]")

    def test_max_attempt_exhaustion_goes_to_dead_letter_once(self):
        self.write_items([item("job-1", max_attempts=1)])
        state = run_job(
            WorkQueue(self.queue_path),
            "job-1",
            AlwaysRetryable(),
            worker="grok",
            dead_letter_path=self.dead_path,
            now=self.now,
        )
        self.assertEqual(state["status"], "dead_letter")
        dead = json.loads(self.dead_path.read_text(encoding="utf-8"))
        self.assertEqual(len(dead["items"]), 1)
        self.assertEqual(dead["items"][0]["job_id"], "job-1")

    def test_provider_failure_does_not_mutate_other_job(self):
        self.write_items([item("bad"), item("good")])
        queue = WorkQueue(self.queue_path)
        run_job(queue, "bad", AlwaysRetryable(), worker="grok", dead_letter_path=self.dead_path, now=self.now)
        good = run_job(queue, "good", MockAdapter(provider="gemini", model="mock"), worker="gemini", dead_letter_path=self.dead_path, now=self.now)
        self.assertEqual(good["status"], "completed")
        data = json.loads(self.queue_path.read_text(encoding="utf-8"))
        states = {entry["id"]: entry["status"] for entry in data["items"]}
        self.assertEqual(states, {"bad": "retryable_failed", "good": "completed"})


if __name__ == "__main__":
    unittest.main()
