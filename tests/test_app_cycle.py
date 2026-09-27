import unittest

from app import poll_interval, run_cycle_once
from runtime.logging_utils import build_log_record
from runtime.settings import Settings


class BrokenWorker:
    def cycle(self):
        raise RuntimeError("SECRET")


class AppCycleTests(unittest.TestCase):
    def test_poll_interval_defaults_to_sixty(self):
        self.assertEqual(poll_interval(Settings.from_env({})), 60)

    def test_cycle_exception_is_contained(self):
        result = run_cycle_once(BrokenWorker())
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["error_code"], "cycle_error")
        self.assertNotIn("SECRET", str(result))

    def test_structured_log_has_only_safe_fields(self):
        row = build_log_record(task_id="A", connector="synthetic", operation="echo", status="succeeded", duration_ms=3, error_code=None)
        self.assertEqual(set(row), {"timestamp", "task_id", "connector", "operation", "status", "duration_ms", "error_code"})


if __name__ == "__main__":
    unittest.main()
