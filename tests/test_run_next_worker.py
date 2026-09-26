import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_next_worker import select_job
from scripts.worker_health import build_health


class NextWorkerTests(unittest.TestCase):
    def test_selects_highest_priority_openai_compatible_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.json"
            path.write_text(json.dumps({"version": 1, "items": [
                {"id": "grok-only", "worker": "grok", "status": "queued", "priority": 100},
                {"id": "low", "worker": "openai", "status": "queued", "priority": 10, "created_at": "2026-09-26T00:00:00+00:00"},
                {"id": "high", "worker": "chatgpt", "status": "queued", "priority": 90, "created_at": "2026-09-26T00:00:00+00:00"},
            ]}), encoding="utf-8")
            self.assertEqual(select_job(path), "high")

    def test_expired_lease_is_reclaimable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "queue.json"
            path.write_text(json.dumps({"version": 1, "items": [{
                "id": "expired", "worker": "openai", "status": "claimed", "priority": 1,
                "claim": {"worker": "old", "lease_expires_at": "2026-09-26T00:00:00+00:00"}
            }]}), encoding="utf-8")
            now = datetime(2026, 9, 26, 1, 0, tzinfo=timezone.utc)
            self.assertEqual(select_job(path, now=now), "expired")


if __name__ == "__main__":
    unittest.main()
