from __future__ import annotations

import hashlib
import json
from typing import Any, Collection, Mapping

from hercules_sentinel.contract import validate_report

_STABLE_EVENT_KEYS = ("provider", "source", "event_type", "repository", "external_id", "run_id", "event_id")


def fingerprint_event(event: Mapping[str, Any]) -> str:
    stable = {key: event.get(key) for key in _STABLE_EVENT_KEYS if event.get(key) is not None}
    encoded = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def evaluate_report(
    report: Mapping[str, Any],
    event: Mapping[str, Any],
    seen_fingerprints: Collection[str],
    contract: Mapping[str, Any],
) -> dict[str, Any]:
    errors = list(validate_report(report, contract))
    fingerprint = fingerprint_event(event)
    duplicate = fingerprint in set(seen_fingerprints)
    if duplicate:
        errors.append("duplicate event fingerprint")

    allowed_repositories = set(contract.get("allowed_repositories") or [])
    event_repository = event.get("repository")
    if event_repository not in allowed_repositories:
        errors.append(f"event repository is outside allowed repository: {event_repository!r}")

    allowed_actions = set(contract.get("allowed_actions") or [])
    actions = []
    if report.get("action") is not None:
        actions.append(str(report.get("action")))
    if event.get("requested_action") is not None:
        actions.append(str(event.get("requested_action")))

    forbidden_actions = [action for action in actions if action not in allowed_actions]
    forbidden = bool(forbidden_actions or report.get("forbidden_action_detected") is True)
    for action in forbidden_actions:
        errors.append(f"forbidden or unsupported pilot action: {action}")

    return {
        "valid": not errors and not forbidden and not duplicate,
        "duplicate": duplicate,
        "forbidden": forbidden,
        "errors": errors,
        "event_fingerprint": fingerprint,
    }
