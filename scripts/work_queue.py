from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

UTC = timezone.utc


class QueueError(RuntimeError):
    pass


class JobNotFound(QueueError):
    pass


class InvalidTransition(QueueError):
    pass


LEGAL_TRANSITIONS = {
    "queued": {"claimed"},
    "retryable_failed": {"claimed", "dead_letter"},
    "claimed": {"completed", "retryable_failed", "blocked", "dead_letter"},
    "completed": {"reviewed"},
    "reviewed": {"applied"},
    "blocked": set(),
    "dead_letter": set(),
    "applied": set(),
}


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class WorkQueue:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def _load(self) -> dict[str, Any]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("version") != 1 or not isinstance(data.get("items"), list):
            raise QueueError("invalid queue document")
        return data

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2, sort_keys=True)
            tmp.write("\n")
            temp_path = Path(tmp.name)
        temp_path.replace(self.path)

    @staticmethod
    def validate_transition(current: str, target: str) -> None:
        if target not in LEGAL_TRANSITIONS.get(current, set()):
            raise InvalidTransition(f"illegal transition: {current} -> {target}")

    @staticmethod
    def _find(data: dict[str, Any], job_id: str) -> dict[str, Any]:
        for entry in data["items"]:
            if entry.get("id") == job_id:
                return entry
        raise JobNotFound(job_id)

    def claim(
        self,
        job_id: str,
        worker: str,
        *,
        now: datetime | None = None,
        lease_seconds: int = 300,
    ) -> dict[str, Any]:
        now = now or datetime.now(UTC)
        data = self._load()
        entry = self._find(data, job_id)
        status = entry.get("status")

        if status == "claimed":
            claim = entry.get("claim") or {}
            expires_at = claim.get("lease_expires_at")
            if not expires_at or _parse(expires_at) > now.astimezone(UTC):
                raise InvalidTransition(f"job {job_id} already has an active claim")
        elif status not in {"queued", "retryable_failed"}:
            raise InvalidTransition(f"cannot claim job in state {status}")

        attempts = int(entry.get("attempt_count", 0))
        max_attempts = int(entry.get("max_attempts", 1))
        if attempts >= max_attempts:
            if status != "claimed":
                self.validate_transition(status, "dead_letter")
            entry["status"] = "dead_letter"
            entry["blocker"] = "max attempts exhausted"
            entry["claim"] = None
            self._save(data)
            raise InvalidTransition(f"job {job_id} exhausted max attempts")

        if status != "claimed":
            self.validate_transition(status, "claimed")
        entry["status"] = "claimed"
        entry["attempt_count"] = attempts + 1
        entry["claim"] = {
            "worker": worker,
            "claimed_at": _iso(now),
            "lease_expires_at": _iso(now + timedelta(seconds=lease_seconds)),
        }
        entry["blocker"] = None
        self._save(data)
        return deepcopy(entry)

    def complete(
        self,
        job_id: str,
        result: dict[str, Any],
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        data = self._load()
        entry = self._find(data, job_id)
        if entry.get("status") == "completed":
            return deepcopy(entry)
        self.validate_transition(entry.get("status"), "completed")
        entry["status"] = "completed"
        entry["result"] = deepcopy(result)
        entry["completed_at"] = _iso(now or datetime.now(UTC))
        entry["claim"] = None
        entry["blocker"] = None
        self._save(data)
        return deepcopy(entry)

    def fail(
        self,
        job_id: str,
        reason: str,
        retryable: bool,
        *,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        data = self._load()
        entry = self._find(data, job_id)
        if entry.get("status") != "claimed":
            raise InvalidTransition(f"cannot fail job in state {entry.get('status')}")

        attempts = int(entry.get("attempt_count", 0))
        max_attempts = int(entry.get("max_attempts", 1))
        if retryable and attempts < max_attempts:
            target = "retryable_failed"
        elif retryable:
            target = "dead_letter"
        else:
            target = "blocked"

        self.validate_transition("claimed", target)
        entry["status"] = target
        entry["blocker"] = reason
        entry["claim"] = None
        entry["failed_at"] = _iso(now or datetime.now(UTC))
        self._save(data)
        return deepcopy(entry)
