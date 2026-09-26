"""Lock / lease-owner tests kept separate from test_work_queue.py to avoid edit races."""
from __future__ import annotations

import json
import tempfile
import threading
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
        "max_attempts": 5,
        "attempt_count": 0,
        "blocker": None,
        "claim": None,
        "result": None,
    }
    base.update(overrides)
    return base


class WorkQueueLockAndLeaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "work_queue.json"
        self.path.write_text(json.dumps({"version": 1, "items": [item()]}), encoding="utf-8")
        self.queue = WorkQueue(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_complete_requires_active_lease_owner(self):
        now = datetime(2026, 9, 26, 3, 1, tzinfo=UTC)
        self.queue.claim("job-1", "grok", now=now)
        with self.assertRaises(InvalidTransition) as ctx:
            self.queue.complete("job-1", {"ok": True}, worker="gemini", now=now)
        self.assertIn("lease owned", str(ctx.exception))

    def test_fail_requires_active_lease_owner(self):
        now = datetime(2026, 9, 26, 3, 1, tzinfo=UTC)
        self.queue.claim("job-1", "grok", now=now)
        with self.assertRaises(InvalidTransition) as ctx:
            self.queue.fail("job-1", "boom", retryable=True, worker="gemini", now=now)
        self.assertIn("lease owned", str(ctx.exception))

    def test_expired_lease_cannot_complete(self):
        now = datetime(2026, 9, 26, 3, 1, tzinfo=UTC)
        self.queue.claim("job-1", "grok", now=now, lease_seconds=30)
        with self.assertRaises(InvalidTransition) as ctx:
            self.queue.complete(
                "job-1",
                {"ok": True},
                worker="grok",
                now=now + timedelta(seconds=31),
            )
        self.assertIn("lease expired", str(ctx.exception))

    def test_concurrent_claims_serialize_to_one_winner(self):
        barrier = threading.Barrier(2)
        results: list[str | Exception] = []
        lock = threading.Lock()

        def attempt(name: str) -> None:
            q = WorkQueue(self.path)
            try:
                barrier.wait(timeout=5)
                claimed = q.claim("job-1", name, now=datetime(2026, 9, 26, 3, 2, tzinfo=UTC))
                with lock:
                    results.append(claimed["claim"]["worker"])
            except Exception as exc:  # noqa: BLE001 — collect for assertion
                with lock:
                    results.append(exc)

        t1 = threading.Thread(target=attempt, args=("grok",))
        t2 = threading.Thread(target=attempt, args=("gemini",))
        t1.start()
        t2.start()
        t1.join(timeout=10)
        t2.join(timeout=10)

        winners = [r for r in results if isinstance(r, str)]
        errors = [r for r in results if isinstance(r, Exception)]
        self.assertEqual(len(winners), 1)
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], InvalidTransition)
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["items"][0]["status"], "claimed")
        self.assertEqual(data["items"][0]["attempt_count"], 1)
        self.assertEqual(data["items"][0]["claim"]["worker"], winners[0])


if __name__ == "__main__":
    unittest.main()
