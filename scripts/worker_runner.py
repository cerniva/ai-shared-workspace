from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from scripts.work_queue import WorkQueue
from scripts.worker_adapters import MissingCredential, NonRetryableProviderError, ProviderNotConfigured, RetryableProviderError

UTC = timezone.utc


def _write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2, sort_keys=True)
        tmp.write("\n")
        temp_path = Path(tmp.name)
    temp_path.replace(path)


def _record_dead_letter(path: Path, state: dict[str, Any], reason: str, now: datetime) -> None:
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = {"version": 1, "items": []}

    key = (state["id"], state.get("attempt_count"))
    for entry in data["items"]:
        if (entry.get("job_id"), entry.get("attempt_count")) == key:
            return

    data["items"].append(
        {
            "job_id": state["id"],
            "project": state.get("project"),
            "worker": state.get("worker"),
            "attempt_count": state.get("attempt_count"),
            "reason": reason,
            "recorded_at": now.astimezone(UTC).isoformat(),
        }
    )
    _write_json_atomic(path, data)


def run_job(
    queue: WorkQueue,
    job_id: str,
    adapter: Any,
    *,
    worker: str,
    dead_letter_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    claimed = queue.claim(job_id, worker, now=now)
    try:
        result = adapter.run(claimed)
    except MissingCredential as exc:
        return queue.fail(job_id, str(exc), retryable=False, now=now)
    except (ProviderNotConfigured, NonRetryableProviderError) as exc:
        return queue.fail(job_id, str(exc), retryable=False, now=now)
    except RetryableProviderError as exc:
        state = queue.fail(job_id, str(exc), retryable=True, now=now)
        if state["status"] == "dead_letter" and dead_letter_path is not None:
            _record_dead_letter(Path(dead_letter_path), state, str(exc), now)
        return state
    except Exception as exc:
        state = queue.fail(job_id, f"unexpected provider error: {exc}", retryable=True, now=now)
        if state["status"] == "dead_letter" and dead_letter_path is not None:
            _record_dead_letter(Path(dead_letter_path), state, str(exc), now)
        return state

    return queue.complete(job_id, result, now=now)
