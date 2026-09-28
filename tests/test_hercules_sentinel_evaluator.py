import unittest

from hercules_sentinel.evaluator import evaluate_report, fingerprint_event


class HerculesSentinelEvaluatorTests(unittest.TestCase):
    def _contract(self):
        return {
            "version": 1,
            "agent_name": "CORE-05 Hercules Sentinel",
            "allowed_repositories": ["cerniva/ai-shared-workspace"],
            "access_mode": "read_only",
            "schedule_enabled": False,
            "required_report_fields": [
                "trigger", "scope", "observed_state", "evidence", "severity",
                "duplicate_or_conflict", "recommended_action", "requires_human",
                "forbidden_action_detected", "cost_or_limit_note",
            ],
            "supported_severities": ["info", "warning", "blocker"],
            "unknown_action_policy": "fail_closed",
            "forbidden_capabilities": [
                "repo_write", "branch_write", "commit_write", "pr_write", "merge",
                "secret_change", "account_security_change", "payment",
                "financial_transaction", "irreversible_publish", "cross_repo_access",
            ],
            "allowed_actions": ["read", "analyze", "recommend"],
        }

    def _event(self, **overrides):
        event = {
            "provider": "github",
            "event_type": "workflow_run",
            "repository": "cerniva/ai-shared-workspace",
            "external_id": "36350519493",
            "timestamp": "2026-09-28T10:00:00Z",
        }
        event.update(overrides)
        return event

    def _report(self, **overrides):
        report = {
            "trigger": {"provider": "github", "event_type": "workflow_run", "external_id": "36350519493"},
            "scope": "cerniva/ai-shared-workspace",
            "observed_state": "worker-orchestration-tests failed",
            "evidence": ["workflow_run:36350519493"],
            "severity": "warning",
            "duplicate_or_conflict": False,
            "recommended_action": "inspect failed step",
            "requires_human": False,
            "forbidden_action_detected": False,
            "cost_or_limit_note": "within configured pilot limits",
            "action": "analyze",
        }
        report.update(overrides)
        return report

    def test_valid_read_only_report_passes(self):
        result = evaluate_report(self._report(), self._event(), set(), self._contract())
        self.assertTrue(result["valid"])
        self.assertFalse(result["duplicate"])
        self.assertFalse(result["forbidden"])
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["event_fingerprint"])

    def test_wrong_repository_fails_closed(self):
        report = self._report(scope="cerniva/grok-chatgpt-masa")
        event = self._event(repository="cerniva/grok-chatgpt-masa")
        result = evaluate_report(report, event, set(), self._contract())
        self.assertFalse(result["valid"])
        self.assertTrue(any("repository" in error or "scope" in error for error in result["errors"]))

    def test_forbidden_merge_request_is_flagged(self):
        result = evaluate_report(
            self._report(action="merge"),
            self._event(requested_action="merge"),
            set(),
            self._contract(),
        )
        self.assertFalse(result["valid"])
        self.assertTrue(result["forbidden"])
        self.assertTrue(any("merge" in error for error in result["errors"]))

    def test_repeated_event_is_duplicate(self):
        event = self._event(timestamp="2026-09-28T10:00:00Z")
        fingerprint = fingerprint_event(event)
        repeated = self._event(timestamp="2026-09-28T10:05:00Z")
        self.assertEqual(fingerprint_event(repeated), fingerprint)
        result = evaluate_report(self._report(), repeated, {fingerprint}, self._contract())
        self.assertTrue(result["duplicate"])
        self.assertFalse(result["valid"])

    def test_unknown_action_fails_closed(self):
        result = evaluate_report(
            self._report(action="teleport"),
            self._event(requested_action="teleport"),
            set(),
            self._contract(),
        )
        self.assertFalse(result["valid"])
        self.assertTrue(result["forbidden"])
        self.assertTrue(any("teleport" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
