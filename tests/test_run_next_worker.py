import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_next_worker import select_job, select_job_info
from scripts.worker_health import build_health

NOW = datetime(2026, 10, 10, 2, 0, tzinfo=timezone.utc)


def _write(tmp, items, name="queue.json"):
    path = Path(tmp) / name
    path.write_text(json.dumps({"version": 1, "items": items}), encoding="utf-8")
    return path


class NextWorkerTests(unittest.TestCase):
    def test_selects_highest_priority_openai_compatible_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, [
                {"id": "grok-only", "worker": "grok", "status": "queued", "priority": 100},
                {"id": "low", "worker": "openai", "status": "queued", "priority": 10, "created_at": "2026-09-26T00:00:00+00:00"},
                {"id": "high", "worker": "chatgpt", "status": "queued", "priority": 90, "created_at": "2026-09-26T00:00:00+00:00"},
            ])
            self.assertEqual(select_job(path), "high")

    def test_retryable_failure_respects_exponential_cooldown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, [{
                "id": "rate-limited", "worker": "openai", "status": "retryable_failed",
                "priority": 100, "attempt_count": 2,
                "failed_at": "2026-09-26T01:00:00+00:00"
            }])
            self.assertIsNone(select_job(path, now=datetime(2026, 9, 26, 1, 29, tzinfo=timezone.utc)))
            self.assertEqual(select_job(path, now=datetime(2026, 9, 26, 1, 30, tzinfo=timezone.utc)), "rate-limited")

    def test_expired_lease_is_reclaimable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, [{
                "id": "expired", "worker": "openai", "status": "claimed", "priority": 1,
                "claim": {"worker": "old", "lease_expires_at": "2026-09-26T00:00:00+00:00"}
            }])
            now = datetime(2026, 9, 26, 1, 0, tzinfo=timezone.utc)
            self.assertEqual(select_job(path, now=now), "expired")

    def test_young_grok_job_not_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, [{"id": "g", "worker": "grok", "status": "queued", "priority": 5,
                                 "created_at": "2026-10-10T01:30:00+00:00"}])
            self.assertIsNone(select_job_info(path, now=NOW))

    def test_old_grok_job_selected_with_fallback_from(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, [{"id": "g", "worker": "grok", "status": "queued", "priority": 5,
                                 "created_at": "2026-10-10T00:30:00+00:00"}])
            self.assertIsNone(select_job_info(path, now=NOW))
            self.assertIsNone(select_job_info(path, now=NOW, fallback_minutes=120))

    def test_provider_health_down_selects_immediately(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, [{"id": "g", "worker": "grok", "status": "queued", "priority": 5,
                                 "created_at": "2026-10-10T01:59:00+00:00"}])
            health = Path(tmp) / "health.json"
            health.write_text(json.dumps({"schema_version": 1, "providers": [
                {"name": "grok", "status": "billing", "http": 403}]}), encoding="utf-8")
            self.assertEqual(select_job_info(path, now=NOW, health_path=health),
                             {"job_id": "g", "fallback_from": "grok"})
            health.write_text("not json", encoding="utf-8")
            self.assertIsNone(select_job_info(path, now=NOW, health_path=health))

    def test_claimed_unexpired_grok_job_not_stolen(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, [{"id": "g", "worker": "grok", "status": "claimed", "priority": 5,
                                 "created_at": "2026-10-09T00:00:00+00:00",
                                 "claim": {"worker": "grok", "lease_expires_at": "2026-10-10T03:00:00+00:00"}}])
            health = Path(tmp) / "health.json"
            health.write_text(json.dumps({"providers": [{"name": "grok", "status": "no_key"}]}), encoding="utf-8")
            self.assertIsNone(select_job_info(path, now=NOW, health_path=health))

    def test_own_job_preferred_over_fallback_at_same_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, [
                {"id": "g", "worker": "grok", "status": "queued", "priority": 5, "created_at": "2026-10-09T00:00:00+00:00"},
                {"id": "own", "worker": "openai", "status": "queued", "priority": 5, "created_at": "2026-10-10T01:00:00+00:00"},
            ])
            self.assertEqual(select_job_info(path, now=NOW), {"job_id": "own"})

    def test_explicit_fallback_workers_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(tmp, [{"id": "g", "worker": "grok", "status": "queued", "priority": 5,
                                 "created_at": "2026-10-10T01:59:00+00:00",
                                 "fallback_workers": ["worker-orchestrator"]}])
            self.assertEqual(select_job_info(path, now=NOW)["fallback_from"], "grok")


if __name__ == "__main__":
    unittest.main()
