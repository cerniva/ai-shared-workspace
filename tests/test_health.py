import unittest

from runtime.health import health_snapshot
from runtime.settings import Settings


class FakeWorker:
    def __init__(self):
        self.settings = Settings.from_env({"GITHUB_TOKEN": "SECRET", "RUNTIME_ID": "r1"})
        self.github_last_ok = True
        self.last_cycle_at = "2026-09-27T00:00:00+00:00"
        self.last_success_at = "2026-09-27T00:00:00+00:00"


class HealthTests(unittest.TestCase):
    def test_health_contains_only_safe_fields(self):
        data = health_snapshot(FakeWorker())
        self.assertEqual(set(data), {"service", "github_configured", "github_last_ok", "last_cycle_at", "last_success_at", "runtime_id"})
        self.assertNotIn("SECRET", str(data))
        self.assertTrue(data["github_configured"])


if __name__ == "__main__":
    unittest.main()
