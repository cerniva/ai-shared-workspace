from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from scripts.runtime_contract import idempotency_key
from runtime.github_client import GitHubConflict

TERMINAL = frozenset({"succeeded", "failed", "blocked"})


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


class StatusStore:
    def __init__(self, data, sha: str, path: str = "state/runtime-status.json"):
        self.data = deepcopy(data)
        self.sha = sha
        self.path = path
        self.dirty: set[str] = set()
        if self.data.get("version") != 1 or not isinstance(self.data.get("items"), list):
            self.data = {"version": 1, "items": []}

    @classmethod
    def from_client(cls, client, path: str = "state/runtime-status.json") -> "StatusStore":
        data, sha = client.get_json(path)
        return cls(data, sha, path)

    def find(self, key: str):
        for item in self.data["items"]:
            if item.get("idempotency_key") == key:
                return deepcopy(item)
        return None

    def is_terminal(self, key: str) -> bool:
        item = self.find(key)
        return bool(item and item.get("status") in TERMINAL)

    def is_active_running(self, key: str, now: datetime, lease_seconds: int = 300) -> bool:
        item = self.find(key)
        if not item or item.get("status") != "running" or not item.get("started_at"):
            return False
        started = datetime.fromisoformat(item["started_at"])
        if started.tzinfo is None:
            started = started.replace(tzinfo=timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)
        return now.astimezone(timezone.utc) < started.astimezone(timezone.utc) + timedelta(seconds=lease_seconds)

    def _upsert(self, item):
        for index, old in enumerate(self.data["items"]):
            if old.get("idempotency_key") == item["idempotency_key"]:
                self.data["items"][index] = deepcopy(item)
                break
        else:
            self.data["items"].append(deepcopy(item))
        self.dirty.add(item["idempotency_key"])
        return deepcopy(item)

    def begin(self, task, now: datetime):
        key = idempotency_key(task)
        existing = self.find(key)
        if existing and existing.get("status") in TERMINAL:
            return existing
        return self._upsert({
            "idempotency_key": key,
            "task_id": task.get("id"),
            "generation": task.get("generation"),
            "connector": task.get("connector"),
            "operation": task.get("operation"),
            "status": "running",
            "started_at": _iso(now),
            "finished_at": None,
            "summary": "",
            "error_code": None,
            "retryable": False,
            "claim_token": uuid4().hex,
        })

    def finish(self, key: str, *, status: str, summary: str, error_code: str | None,
               retryable: bool, now: datetime):
        item = self.find(key) or {"idempotency_key": key}
        item.update({
            "status": status,
            "summary": summary,
            "error_code": error_code,
            "retryable": bool(retryable),
            "finished_at": _iso(now),
        })
        return self._upsert(item)

    @staticmethod
    def _claim_conflicts(local_item, remote_item) -> bool:
        if not remote_item:
            return False
        local_token = local_item.get("claim_token")
        remote_token = remote_item.get("claim_token")
        remote_status = remote_item.get("status")
        local_status = local_item.get("status")

        if local_status == "running":
            if remote_status in TERMINAL:
                return True
            if remote_status == "running":
                return not local_token or not remote_token or local_token != remote_token
            return True

        if local_status in TERMINAL:
            if remote_status in TERMINAL:
                return not local_token or not remote_token or local_token != remote_token
            if remote_status == "running":
                return not local_token or not remote_token or local_token != remote_token
        return False

    def merge_and_write(self, client, max_attempts: int = 3) -> bool:
        for _ in range(max_attempts):
            latest, sha = client.get_json(self.path)
            merged = deepcopy(latest)
            if merged.get("version") != 1 or not isinstance(merged.get("items"), list):
                merged = {"version": 1, "items": []}

            remote_index = {item.get("idempotency_key"): item for item in merged["items"]}
            local_index = {item.get("idempotency_key"): item for item in self.data["items"]}
            rejected = False
            for key in self.dirty:
                local_item = local_index[key]
                remote_item = remote_index.get(key)
                if self._claim_conflicts(local_item, remote_item):
                    rejected = True
                    continue
                remote_index[key] = deepcopy(local_item)

            if rejected:
                merged["items"] = list(remote_index.values())
                self.data = merged
                self.sha = sha
                self.dirty.clear()
                return False

            merged["items"] = list(remote_index.values())
            try:
                new_sha = client.put_json(self.path, merged, sha, "runtime: update sanitized status")
            except GitHubConflict:
                continue
            self.data = merged
            self.sha = new_sha
            self.dirty.clear()
            return True
        raise GitHubConflict("github content conflict")
