#!/usr/bin/env python3
"""No-external-side-effect smoke check for the health controller contracts."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from tempfile import TemporaryDirectory
from pathlib import Path

try:
    from scripts.health_controller import decide_and_record
    from scripts.provider_router import ProviderCandidate, select_provider
    from scripts.system_health import HealthEvidence, effective_status
except ImportError:
    from health_controller import decide_and_record
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
    with TemporaryDirectory() as temp_dir:
        event_log = Path(temp_dir) / "health-decisions.jsonl"
        decision = decide_and_record(
            failed,
            target="scripts/worker_runner.py",
            repair="restart_worker",
            event_log=event_log,
        )
        assert decision.action == "repair_then_retest" and decision.requires_retest
        protected = decide_and_record(
            failed,
            target="PayoutLens/app.py",
            repair="restart_worker",
            event_log=event_log,
        )
        assert protected.action == "protected"
        records = [json.loads(line) for line in event_log.read_text(encoding="utf-8").splitlines()]
        assert len(records) == 2
        assert all(record["event_key"].startswith("health_decision:") for record in records)
    print("self-healing-health-controller smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
