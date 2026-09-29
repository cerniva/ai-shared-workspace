#!/usr/bin/env python3
"""Fail-closed self-healing decision engine."""
from __future__ import annotations

from dataclasses import dataclass

try:
    from scripts.system_health import HealthEvidence, is_protected_target
except ImportError:
    from system_health import HealthEvidence, is_protected_target

SAFE_REPAIRS = {"restart_worker", "reconcile_state", "refresh_health", "rerun_failed_job"}


@dataclass(frozen=True)
class ControllerDecision:
    action: str
    reason: str
    requires_retest: bool = False


def decide_action(evidence: HealthEvidence, *, target: str, repair: str | None = None) -> ControllerDecision:
    if is_protected_target(target):
        return ControllerDecision("protected", "payoutlens_excluded")
    if evidence.status == "external_wait":
        return ControllerDecision("wait_external", "external_dependency")
    if evidence.status == "disabled_optional":
        return ControllerDecision("no_action", "optional_provider_disabled")
    if evidence.status == "healthy":
        return ControllerDecision("no_action", "healthy")
    if evidence.status == "degraded":
        return ControllerDecision("retest", "degraded_requires_fresh_evidence", True)
    if evidence.status != "failed":
        return ControllerDecision("manual_review", "unknown_status")
    if repair not in SAFE_REPAIRS:
        return ControllerDecision("manual_review", "repair_not_allowlisted")
    return ControllerDecision("repair_then_retest", repair or "safe_repair", True)
