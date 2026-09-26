"""Move 429 dead-letters back to retryable_failed without counting as a new claim."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from scripts.work_queue import InvalidTransition, WorkQueue

UTC = timezone.utc
RATE_MARKERS = ("429", "rate_limited", "rate limit")


def is_rate_limited_reason(reason: str | None) -> bool:
    text = (reason or "").lower()
    return any(marker in text for marker in RATE_MARKERS)


class WorkQueueWithRequeue(WorkQueue):
    def requeue_rate_limited(
        self,
        job_id: str,
        *,
        extra_attempts: int = 3,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        now = now or datetime.now(UTC)
        with self._locked():
            data = self._load()
            entry = self._find(data, job_id)
            if entry.get("status") != "dead_letter":
                raise InvalidTransition(f"cannot requeue from {entry.get('status')}")
            if not is_rate_limited_reason(entry.get("blocker")):
                raise InvalidTransition("dead_letter is not rate-limited")
            extra = max(1, int(extra_attempts))
            entry["status"] = "retryable_failed"
            entry["max_attempts"] = int(entry.get("max_attempts", 1)) + extra
            entry["blocker"] = "rate_limited: waiting for retry"
            entry["claim"] = None
            entry["requeued_at"] = now.astimezone(UTC).isoformat()
            self._save(data)
            return dict(entry)
