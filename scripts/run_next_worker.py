from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.provider_config import make_failover_adapter
from scripts.work_queue import WorkQueue, _parse
from scripts.worker_runner import run_job

UTC = timezone.utc

OWN_WORKERS = {"openai", "chatgpt", "any", None}
SELF_NAME = "worker-orchestrator"
DEFAULT_FALLBACK_MINUTES = 60
DOWN_STATUSES = {
    "no_key", "billing", "quota", "payment", "payment_required", "auth",
    "auth_error", "unauthorized", "forbidden", "invalid_key", "insufficient_quota",
}
# Map queue worker names to provider_health provider names.
WORKER_PROVIDER = {"grok": "grok", "xai": "grok", "claude": "claude", "anthropic": "claude",
                   "gemini": "gemini", "google": "gemini", "deepseek": "deepseek",
                   "mistral": "mistral", "groq": "groq"}


def load_down_providers(path: Path | None) -> set[str]:
    """Providers marked not working in provider_health.json; empty on any problem."""
    if path is None:
        return set()
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        down = set()
        for p in data.get("providers", []):
            if isinstance(p, dict) and str(p.get("status", "")).lower() in DOWN_STATUSES:
                down.add(str(p.get("name")))
        return down
    except Exception:
        return set()


def _status_ok(entry: dict, now: datetime) -> bool:
    status = entry.get("status")
    if status == "queued":
        return True
    if status == "retryable_failed":
        failed_at = entry.get("failed_at")
        if not failed_at:
            return True
        attempts = max(1, int(entry.get("attempt_count", 1)))
        # Exponential cooldown for provider throttling: 15, 30, 60, 120... minutes.
        cooldown_minutes = min(240, 15 * (2 ** (attempts - 1)))
        return _parse(failed_at) + timedelta(minutes=cooldown_minutes) <= now
    if status == "claimed":
        expires = (entry.get("claim") or {}).get("lease_expires_at")
        return bool(expires and _parse(expires) <= now)
    return False


def _fallback_reason(entry: dict, now: datetime, fallback_minutes: float, down: set[str]) -> bool:
    """Whether a job owned by another worker may be taken over by this worker."""
    fallbacks = entry.get("fallback_workers", [])
    # Explicit opt-in (chatgpt/fix-explicit-fallback-worker-20261010).
    if isinstance(fallbacks, list) and SELF_NAME in fallbacks:
        return True
    worker = str(entry.get("worker"))
    if WORKER_PROVIDER.get(worker, worker) in down:
        return True
    # Age alone never authorizes taking another worker's queued job.
    # Only explicit fallback opt-in or a verified down provider may transfer ownership.
    return False


def _eligible(entry: dict, now: datetime, fallback_minutes: float = DEFAULT_FALLBACK_MINUTES,
              down: set[str] | None = None) -> bool:
    if entry.get("worker") not in OWN_WORKERS:
        if not _fallback_reason(entry, now, fallback_minutes, down or set()):
            return False
    return _status_ok(entry, now)


def select_job_info(queue_path: Path, now: datetime | None = None,
                    fallback_minutes: float = DEFAULT_FALLBACK_MINUTES,
                    health_path: Path | None = None) -> dict | None:
    now = now or datetime.now(UTC)
    down = load_down_providers(health_path)
    data = json.loads(queue_path.read_text(encoding="utf-8"))
    candidates = [i for i in data.get("items", []) if _eligible(i, now, fallback_minutes, down)]
    if not candidates:
        return None
    candidates.sort(key=lambda x: (-int(x.get("priority", 0)),
                                   0 if x.get("worker") in OWN_WORKERS else 1,
                                   x.get("created_at", ""), x.get("id", "")))
    best = candidates[0]
    info = {"job_id": str(best["id"])}
    if best.get("worker") not in OWN_WORKERS:
        info["fallback_from"] = best.get("worker")
    return info


def select_job(queue_path: Path, now: datetime | None = None,
               fallback_minutes: float = DEFAULT_FALLBACK_MINUTES,
               health_path: Path | None = None) -> str | None:
    info = select_job_info(queue_path, now, fallback_minutes, health_path)
    return info["job_id"] if info else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default="state/work_queue.json")
    parser.add_argument("--dead-letter", default="state/dead_letter.json")
    parser.add_argument("--provider-health", default="state/provider_health.json")
    parser.add_argument("--fallback-minutes", type=float,
                        default=float(os.environ.get("WORKER_FALLBACK_MINUTES") or DEFAULT_FALLBACK_MINUTES))
    args = parser.parse_args()
    queue_path = Path(args.queue)
    health = Path(args.provider_health)
    info = select_job_info(queue_path, fallback_minutes=args.fallback_minutes,
                           health_path=health if health.exists() else None)
    if info is None:
        print(json.dumps({"status": "idle"}))
        return
    job_id = info["job_id"]
    if "fallback_from" in info:
        print(json.dumps({"event": "fallback_selected", **info}, ensure_ascii=False))
    state = run_job(
        WorkQueue(queue_path),
        job_id,
        make_failover_adapter(),
        worker=SELF_NAME,
        dead_letter_path=Path(args.dead_letter),
    )
    out = {"status": state.get("status"), "job_id": job_id}
    if "fallback_from" in info:
        out["fallback_from"] = info["fallback_from"]
    print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
