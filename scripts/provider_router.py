#!/usr/bin/env python3
"""Deterministic free-first provider selection."""
from __future__ import annotations

from dataclasses import dataclass

BLOCKED_FAILURES = {"auth", "billing", "oauth", "payment", "account_consent"}
COST_ORDER = {"local_free": 0, "cloud_free": 1, "paid": 2}


@dataclass(frozen=True)
class ProviderCandidate:
    name: str
    cost_class: str
    healthy: bool
    failure_class: str | None = None


def select_provider(candidates: list[ProviderCandidate], *, allow_paid: bool = False) -> ProviderCandidate | None:
    eligible = []
    for candidate in candidates:
        if not candidate.healthy or candidate.failure_class in BLOCKED_FAILURES:
            continue
        if candidate.cost_class == "paid" and not allow_paid:
            continue
        if candidate.cost_class not in COST_ORDER:
            continue
        eligible.append(candidate)
    if not eligible:
        return None
    return min(eligible, key=lambda item: (COST_ORDER[item.cost_class], item.name))
