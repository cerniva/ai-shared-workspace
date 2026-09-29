#!/usr/bin/env python3
"""Evidence-based component health with stale-green protection."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite

VALID_STATUSES = {"healthy", "degraded", "external_wait", "disabled_optional", "failed"}


@dataclass(frozen=True)
class HealthEvidence:
    component: str
    status: str
    checked_at: str
    detail: str = ""
    evidence_kind: str = "smoke_test"
    ttl_seconds: int = 3600


def is_protected_target(target: str) -> bool:
    return "payoutlens" in str(target).casefold()


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def effective_status(evidence: HealthEvidence, *, now: datetime | None = None) -> tuple[str, str]:
    if evidence.status not in VALID_STATUSES:
        return "failed", "unknown_status"
    if evidence.status != "healthy":
        return evidence.status, evidence.detail or evidence.status
    try:
        checked = _parse_time(evidence.checked_at)
    except (AttributeError, TypeError, ValueError):
        return "failed", "invalid_evidence_timestamp"
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)
    if checked > current:
        return "failed", "future_evidence_timestamp"
    try:
        ttl = float(evidence.ttl_seconds)
        if not isfinite(ttl):
            return "failed", "invalid_ttl"
        stale = ttl < 0 or (current - checked).total_seconds() > ttl
    except (TypeError, ValueError, OverflowError):
        return "failed", "invalid_ttl"
    if stale:
        return "degraded", "stale_green"
    return "healthy", evidence.detail or "fresh_evidence"
