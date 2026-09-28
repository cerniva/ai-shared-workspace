from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from scripts.observability import emit_event
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


def _observe(event_name: str, state: dict[str, Any], now: datetime, *, error: str | None = None, exception: BaseException | None = None) -> None:
    payload: dict[str, Any] = {
        "job_id": state.get("id"),
        "project": state.get("project"),
        "worker": state.get("worker"),
        "attempt_count": state.get("attempt_count"),
        "status": state.get("status"),
    }
    if error is not None:
        payload["error"] = error
    emit_event(event_name, payload, exception=exception, timestamp=now)


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
    _observe("worker.started", claimed, now)
    try:
        result = adapter.run(claimed)
    except MissingCredential as exc:
        state = queue.fail(job_id, str(exc), retryable=False, worker=worker, now=now)
        _observe(f"worker.{state['status']}", state, now, error=str(exc), exception=exc)
        return state
    except (ProviderNotConfigured, NonRetryableProviderError) as exc:
        state = queue.fail(job_id, str(exc), retryable=False, worker=worker, now=now)
        _observe(f"worker.{state['status']}", state, now, error=str(exc), exception=exc)
        return state
    except RetryableProviderError as exc:
        state = queue.fail(job_id, str(exc), retryable=True, worker=worker, now=now)
        if state["status"] == "dead_letter" and dead_letter_path is not None:
            _record_dead_letter(Path(dead_letter_path), state, str(exc), now)
        _observe(f"worker.{state['status']}", state, now, error=str(exc), exception=exc)
        return state
    except Exception as exc:
        message = f"unexpected provider error: {exc}"
        state = queue.fail(job_id, message, retryable=True, worker=worker, now=now)
        if state["status"] == "dead_letter" and dead_letter_path is not None:
            _record_dead_letter(Path(dead_letter_path), state, str(exc), now)
        _observe(f"worker.{state['status']}", state, now, error=message, exception=exc)
        return state

    state = queue.complete(job_id, result, worker=worker, now=now)
    _observe("worker.completed", state, now)
    return state
