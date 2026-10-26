"""Fail-closed same-day upload attempt gate: no API or paid-service tests."""
import unittest
from datetime import datetime, timezone

from scripts.shorts_upload_daily_gate import assert_first_attempt_today

NOW = datetime(2026, 10, 26, 14, 17, tzinfo=timezone.utc)


def run(run_id, created):
    return {"id": run_id, "created_at": created}


class DailyGateTests(unittest.TestCase):
    def check(self, rows, current=10):
        return assert_first_attempt_today(
            "cerniva/ai-shared-workspace", current, "fake-test-token", now=NOW,
            fetch=lambda url, token: {"workflow_runs": rows})

    def test_first_attempt_allowed_when_current_run_visible(self):
        value = self.check([run(10, "2026-10-26T14:16:00Z"),
                            run(9, "2026-10-25T23:00:00Z")])
        self.assertEqual(value["gate"], "PASS")
        self.assertEqual(value["day"], "2026-10-26")

    def test_second_attempt_same_istanbul_day_blocked(self):
        with self.assertRaisesRegex(RuntimeError, "DAILY_UPLOAD_ATTEMPT_BLOCKED"):
            self.check([run(10, "2026-10-26T14:16:00Z"),
                        run(8, "2026-10-25T22:00:00Z")])

    def test_prior_failed_or_cancelled_attempt_also_blocks(self):
        with self.assertRaisesRegex(RuntimeError, "DAILY_UPLOAD_ATTEMPT_BLOCKED"):
            self.check([run(10, "2026-10-26T14:16:00Z"),
                        run(7, "2026-10-26T03:00:00Z")])

    def test_no_current_run_blocks(self):
        with self.assertRaisesRegex(RuntimeError, "GITHUB_RUNS_UNVERIFIED"):
            self.check([run(9, "2026-10-25T12:00:00Z")])

    def test_malformed_response_blocks(self):
        with self.assertRaisesRegex(RuntimeError, "GITHUB_RUNS_UNVERIFIED"):
            assert_first_attempt_today("a/b", 10, "test", now=NOW,
                                       fetch=lambda u, t: {"workflow_runs": None})

    def test_api_failure_propagates_fail_closed(self):
        def unavailable(u, t):
            raise OSError("offline")
        with self.assertRaisesRegex(OSError, "offline"):
            assert_first_attempt_today("a/b", 10, "test", now=NOW, fetch=unavailable)

    def test_missing_auth_blocks(self):
        with self.assertRaises(ValueError):
            assert_first_attempt_today("a/b", 10, "", now=NOW, fetch=lambda u, t: {})


if __name__ == "__main__":
    unittest.main()
