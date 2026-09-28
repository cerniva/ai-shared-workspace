import json
import tempfile
import unittest
from pathlib import Path

from hercules_sentinel.contract import load_contract, validate_contract, validate_report


class HerculesSentinelContractTests(unittest.TestCase):
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

    def _report(self):
        return {
            "trigger": {"provider": "github", "event_type": "workflow_run", "external_id": "123"},
            "scope": "cerniva/ai-shared-workspace",
            "observed_state": "workflow failed",
            "evidence": ["run:123"],
            "severity": "warning",
            "duplicate_or_conflict": False,
            "recommended_action": "inspect failed step",
            "requires_human": False,
            "forbidden_action_detected": False,
            "cost_or_limit_note": "within pilot cap",
            "action": "analyze",
        }

    def test_contract_is_single_repo_read_only(self):
        contract = self._contract()
        self.assertEqual(validate_contract(contract), [])
        self.assertEqual(contract["allowed_repositories"], ["cerniva/ai-shared-workspace"])
        self.assertEqual(contract["access_mode"], "read_only")
        self.assertEqual(contract["agent_name"], "CORE-05 Hercules Sentinel")

    def test_contract_disables_schedule(self):
        contract = self._contract()
        self.assertFalse(contract["schedule_enabled"])
        self.assertEqual(validate_contract(contract), [])

    def test_contract_requires_output_fields(self):
        contract = self._contract()
        expected = {
            "trigger", "scope", "observed_state", "evidence", "severity",
            "duplicate_or_conflict", "recommended_action", "requires_human",
            "forbidden_action_detected", "cost_or_limit_note",
        }
        self.assertEqual(set(contract["required_report_fields"]), expected)
        self.assertEqual(validate_contract(contract), [])

    def test_contract_rejects_wrong_repo(self):
        contract = self._contract()
        contract["allowed_repositories"] = ["cerniva/grok-chatgpt-masa"]
        errors = validate_contract(contract)
        self.assertTrue(any("allowed_repositories" in error for error in errors))

    def test_report_rejects_missing_evidence(self):
        contract = self._contract()
        report = self._report()
        del report["evidence"]
        errors = validate_report(report, contract)
        self.assertTrue(any("evidence" in error for error in errors))

    def test_report_rejects_unknown_severity(self):
        contract = self._contract()
        report = self._report()
        report["severity"] = "critical"
        errors = validate_report(report, contract)
        self.assertTrue(any("severity" in error for error in errors))

    def test_load_contract_requires_json_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "contract.json"
            path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_contract(path)


if __name__ == "__main__":
    unittest.main()
