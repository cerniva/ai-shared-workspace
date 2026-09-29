#!/usr/bin/env python3
"""No-side-effect smoke check for the health controller contracts."""
from __future__ import annotations

from datetime import datetime, timezone

try:
    from scripts.health_controller import decide_action
    from scripts.provider_router import ProviderCandidate, select_provider
    from scripts.system_health import HealthEvidence, effective_status
except ImportError:
    from health_controller import decide_action
    from provider_router import ProviderCandidate, select_provider
    from system_health import HealthEvidence, effective_status


def main() -> int:
    now = datetime.now(timezone.utc)
    health = HealthEvidence("worker", "healthy", now.isoformat(), ttl_seconds=300)
    assert effective_status(health, now=now)[0] == "healthy"
    provider = select_provider([
        ProviderCandidate("paid", "paid", True),
        ProviderCandidate("free", "cloud_free", True),
    ])
    assert provider and provider.name == "free"
    failed = HealthEvidence("worker", "failed", now.isoformat())
    decision = decide_action(failed, target="scripts/worker_runner.py", repair="restart_worker")
    assert decision.action == "repair_then_retest" and decision.requires_retest
    protected = decide_action(failed, target="PayoutLens/app.py", repair="restart_worker")
    assert protected.action == "protected"
    print("self-healing-health-controller smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
