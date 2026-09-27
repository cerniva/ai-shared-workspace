from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    reason: str
    code: str


ALLOWED = frozenset({("synthetic", "echo")})
SAFE_CLASSES = frozenset({"read", "prepare"})


def classify_task(task) -> PolicyDecision:
    action_class = task.get("action_class")
    pair = (task.get("connector"), task.get("operation"))
    if action_class not in SAFE_CLASSES:
        return PolicyDecision(False, "action class blocked", "action_class_blocked")
    if pair not in ALLOWED:
        return PolicyDecision(False, "connector/operation blocked", "operation_blocked")
    return PolicyDecision(True, "allowlisted v1 operation", "allowed")
