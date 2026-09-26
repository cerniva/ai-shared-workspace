from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.provider_config import make_failover_adapter
from scripts.work_queue import WorkQueue, _parse
from scripts.worker_runner import run_job

UTC = timezone.utc


def _eligible(entry: dict, now: datetime) -> bool:
    if entry.get("worker") not in {"openai", "chatgpt", "any", None}:
        return False
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


def select_job(queue_path: Path, now: datetime | None = None) -> str | None:
    now = now or datetime.now(UTC)
    data = json.loads(queue_path.read_text(encoding="utf-8"))
    candidates = [item for item in data.get("items", []) if _eligible(item, now)]
    if not candidates:
        return None
    candidates.sort(key=lambda x: (-int(x.get("priority", 0)), x.get("created_at", ""), x.get("id", "")))
    return str(candidates[0]["id"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default="state/work_queue.json")
    parser.add_argument("--dead-letter", default="state/dead_letter.json")
    args = parser.parse_args()
    queue_path = Path(args.queue)
    job_id = select_job(queue_path)
    if job_id is None:
        print(json.dumps({"status": "idle"}))
        return
    state = run_job(
        WorkQueue(queue_path),
        job_id,
        make_failover_adapter(),
        worker="openai",
        dead_letter_path=Path(args.dead_letter),
    )
    print(json.dumps({"status": state.get("status"), "job_id": job_id}, ensure_ascii=False))


if __name__ == "__main__":
    main()
