from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

EXPECTED_REPOSITORIES = ["cerniva/ai-shared-workspace"]
EXPECTED_AGENT_NAME = "CORE-05 Hercules Sentinel"
EXPECTED_ACCESS_MODE = "read_only"
EXPECTED_SEVERITIES = {"info", "warning", "blocker"}
EXPECTED_REPORT_FIELDS = {
    "trigger",
    "scope",
    "observed_state",
    "evidence",
    "severity",
    "duplicate_or_conflict",
    "recommended_action",
    "requires_human",
    "forbidden_action_detected",
    "cost_or_limit_note",
}
EXPECTED_ALLOWED_ACTIONS = {"read", "analyze", "recommend"}
EXPECTED_FORBIDDEN = {
    "repo_write",
    "branch_write",
    "commit_write",
    "pr_write",
    "merge",
    "secret_change",
    "account_security_change",
    "payment",
    "financial_transaction",
    "irreversible_publish",
    "cross_repo_access",
}


def load_contract(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Hercules Sentinel contract must be a JSON object")
    return data


def validate_contract(contract: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if contract.get("version") != 1:
        errors.append("version must be 1")
    if contract.get("agent_name") != EXPECTED_AGENT_NAME:
        errors.append(f"agent_name must be {EXPECTED_AGENT_NAME!r}")
    if contract.get("allowed_repositories") != EXPECTED_REPOSITORIES:
        errors.append("allowed_repositories must be exactly ['cerniva/ai-shared-workspace']")
    if contract.get("access_mode") != EXPECTED_ACCESS_MODE:
        errors.append("access_mode must be read_only")
    if contract.get("schedule_enabled") is not False:
        errors.append("schedule_enabled must be false during pilot")
    if set(contract.get("required_report_fields") or []) != EXPECTED_REPORT_FIELDS:
        errors.append("required_report_fields do not match the pilot contract")
    if set(contract.get("supported_severities") or []) != EXPECTED_SEVERITIES:
        errors.append("supported_severities must be info, warning, blocker")
    if contract.get("unknown_action_policy") != "fail_closed":
        errors.append("unknown_action_policy must be fail_closed")
    if set(contract.get("forbidden_capabilities") or []) != EXPECTED_FORBIDDEN:
        errors.append("forbidden_capabilities do not match the pilot contract")
    if set(contract.get("allowed_actions") or []) != EXPECTED_ALLOWED_ACTIONS:
        errors.append("allowed_actions must be read, analyze, recommend")
    return errors


def validate_report(report: Mapping[str, Any], contract: Mapping[str, Any]) -> list[str]:
    errors = validate_contract(contract)
    required = set(contract.get("required_report_fields") or [])
    for field in sorted(required):
        if field not in report:
            errors.append(f"missing required report field: {field}")

    allowed_repositories = contract.get("allowed_repositories") or []
    scope = report.get("scope")
    if scope is not None and scope not in allowed_repositories:
        errors.append(f"scope is outside allowed repository: {scope!r}")

    severity = report.get("severity")
    supported = set(contract.get("supported_severities") or [])
    if severity is not None and severity not in supported:
        errors.append(f"unsupported severity: {severity!r}")

    if "requires_human" in report and not isinstance(report.get("requires_human"), bool):
        errors.append("requires_human must be boolean")
    if "forbidden_action_detected" in report and not isinstance(report.get("forbidden_action_detected"), bool):
        errors.append("forbidden_action_detected must be boolean")
    if "duplicate_or_conflict" in report and not isinstance(report.get("duplicate_or_conflict"), bool):
        errors.append("duplicate_or_conflict must be boolean")

    evidence = report.get("evidence")
    if "evidence" in report and not isinstance(evidence, (str, list, dict)):
        errors.append("evidence must be a string, list, or object")

    return errors
