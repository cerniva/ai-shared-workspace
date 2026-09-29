from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from scripts.work_queue import _parse

UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[1]
PROVIDER_ENV = (
    ("gemini", "GEMINI_API_KEY"),
    ("openai", "OPENAI_API_KEY"),
    ("grok", "XAI_API_KEY"),
    ("meta", "META_MODEL_API_KEY"),
)


def build_health(now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    queue_path = ROOT / "state" / "work_queue.json"
    dead_path = ROOT / "state" / "dead_letter.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    dead = json.loads(dead_path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    active_leases = []
    last_success = None
    for item in queue.get("items", []):
        status = str(item.get("status"))
        counts[status] = counts.get(status, 0) + 1
        claim = item.get("claim") or {}
        expires = claim.get("lease_expires_at")
        if status == "claimed" and expires and _parse(expires) > now:
            active_leases.append({"job_id": item.get("id"), "worker": claim.get("worker"), "lease_expires_at": expires})
        if status in {"completed", "reviewed", "applied"}:
            stamp = item.get("completed_at") or item.get("reviewed_at") or item.get("applied_at")
            if stamp and (last_success is None or stamp > last_success):
                last_success = stamp

    configured = {provider: bool(os.environ.get(name, "").strip()) for provider, name in PROVIDER_ENV}
    return {
        "generated_at": now.isoformat(),
        "healthy": bool(queue.get("version") == 1 and dead.get("version") == 1),
        "health_scope": "queue-and-dead-letter-structure-only",
        "provider_readiness_checked": False,
        "provider_note": "Credential presence is configuration evidence only; provider HTTP/quota/readiness is tracked separately and this snapshot makes no live provider-health claim.",
        "model": {
            "provider": "openai",
            "model": os.environ.get("OPENAI_MODEL", "gpt-5.6-sol"),
            "credential_configured": configured["openai"],
            "readiness_checked": False,
        },
        "routing": {
            "worker_failover_order": ["gemini", "openai", "grok", "meta"],
            "configured_worker_providers": configured,
        },
        "github": {"actions_repository": os.environ.get("GITHUB_REPOSITORY"), "token_available": bool(os.environ.get("GITHUB_TOKEN"))},
        "queue": {"counts": counts, "active_leases": active_leases},
        "last_successful_work": last_success,
        "dead_letter_count": len(dead.get("items", [])),
        "failed_or_blocked": counts.get("retryable_failed", 0) + counts.get("blocked", 0) + counts.get("dead_letter", 0),
    }


def main() -> None:
    print(json.dumps(build_health(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
