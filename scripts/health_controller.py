#!/usr/bin/env python3
"""Fail-closed self-healing decision engine."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from scripts.health_observability import append_local_event
    from scripts.system_health import HealthEvidence, effective_status, is_protected_target
except ImportError:
    from health_observability import append_local_event
    from system_health import HealthEvidence, effective_status, is_protected_target

SAFE_REPAIRS = {"restart_worker", "reconcile_state", "refresh_health", "rerun_failed_job"}


@dataclass(frozen=True)
class ControllerDecision:
    action: str
    reason: str
    requires_retest: bool = False


def decide_action(evidence: HealthEvidence, *, target: str, repair: str | None = None) -> ControllerDecision:
    if is_protected_target(target):
        return ControllerDecision("protected", "payoutlens_excluded")
    status, status_reason = effective_status(evidence)
    if status == "external_wait":
        return ControllerDecision("wait_external", "external_dependency")
    if status == "disabled_optional":
        return ControllerDecision("no_action", "optional_provider_disabled")
    if status == "healthy":
        return ControllerDecision("no_action", "healthy")
    if status == "degraded":
        return ControllerDecision("retest", status_reason or "degraded_requires_fresh_evidence", True)
    if status != "failed" or status_reason == "unknown_status":
        return ControllerDecision("manual_review", "unknown_status")
    if repair not in SAFE_REPAIRS:
        return ControllerDecision("manual_review", "repair_not_allowlisted")
    return ControllerDecision("repair_then_retest", repair or "safe_repair", True)


def decide_and_record(
    evidence: HealthEvidence,
    *,
    target: str,
    event_log: str | Path,
    repair: str | None = None,
) -> ControllerDecision:
    """Make one decision and durably append its canonical local evidence."""
    decision = decide_action(evidence, target=target, repair=repair)
    event = {
        "event_key": f"health_decision:{evidence.component}:{target}:{evidence.checked_at}:{decision.action}",
        "component": evidence.component,
        "target": target,
        "checked_at": evidence.checked_at,
        "decision": asdict(decision),
    }
    append_local_event(event_log, event)
    return decision
