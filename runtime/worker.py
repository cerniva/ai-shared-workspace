from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone

from scripts.runtime_contract import idempotency_key, validate_dispatch_document, validate_dispatch_item
from runtime.connectors import SyntheticConnector
from runtime.github_client import GitHubContentsClient
from runtime.logging_utils import build_log_record, emit_log
from runtime.policy import classify_task
from runtime.redaction import redact_text, sanitize_object
from runtime.status_store import StatusStore


@dataclass
class CycleReport:
    succeeded: int = 0
    failed: int = 0
    blocked: int = 0
    skipped: int = 0
    unready: bool = False


class RuntimeWorker:
    def __init__(self, settings, client=None, connectors=None, log_sink=None):
        self.settings = settings
        self.client = client
        self.connectors = connectors or {"synthetic": SyntheticConnector()}
        self.log_sink = log_sink or emit_log
        self.github_last_ok = False
        self.last_cycle_at = None
        self.last_success_at = None

    @staticmethod
    def _now(now=None):
        return now or datetime.now(timezone.utc)

    def _emit(self, task, *, status: str, error_code: str | None, started: float) -> None:
        row = build_log_record(
            task_id=task.get("id"),
            connector=task.get("connector"),
            operation=task.get("operation"),
            status=status,
            duration_ms=max(0, int((time.monotonic() - started) * 1000)),
            error_code=error_code,
        )
        safe_row = sanitize_object(row, [self.settings.github_token])
        try:
            self.log_sink(safe_row)
        except Exception:
            pass

    def cycle(self, now=None) -> CycleReport:
        now = self._now(now)
        self.last_cycle_at = now.isoformat()
        report = CycleReport()

        if not self.settings.ready_for_github:
            report.unready = True
            return report

        client = self.client or GitHubContentsClient(self.settings)
        dispatch, _ = client.get_json("tasks/runtime-dispatch.json")
        self.github_last_ok = True

        document_errors = validate_dispatch_document(dispatch)
        if document_errors:
            if isinstance(dispatch, dict) and isinstance(dispatch.get("items"), list):
                report.blocked += max(1, len(dispatch["items"]))
            else:
                report.blocked += 1
            return report

        store = StatusStore.from_client(client)
        for task in dispatch["items"]:
            started = time.monotonic()
            errors = validate_dispatch_item(task)
            key = None
            if isinstance(task.get("id"), str) and isinstance(task.get("generation"), int):
                key = idempotency_key(task)

            if key and (store.is_terminal(key) or store.is_active_running(key, now)):
                report.skipped += 1
                self._emit(task, status="skipped", error_code=None, started=started)
                continue

            if errors:
                report.blocked += 1
                if key:
                    store.begin(task, now)
                    if not store.merge_and_write(client):
                        report.skipped += 1
                        report.blocked -= 1
                        self._emit(task, status="skipped", error_code="claim_lost", started=started)
                        continue
                    store.finish(
                        key,
                        status="blocked",
                        summary=redact_text("; ".join(errors), [self.settings.github_token]),
                        error_code="invalid_task",
                        retryable=False,
                        now=now,
                    )
                    store.merge_and_write(client)
                self._emit(task, status="blocked", error_code="invalid_task", started=started)
                continue

            decision = classify_task(task)
            key = idempotency_key(task)
            if not decision.allowed:
                store.begin(task, now)
                if not store.merge_and_write(client):
                    report.skipped += 1
                    self._emit(task, status="skipped", error_code="claim_lost", started=started)
                    continue
                store.finish(
                    key,
                    status="blocked",
                    summary=decision.reason,
                    error_code=decision.code,
                    retryable=False,
                    now=now,
                )
                store.merge_and_write(client)
                report.blocked += 1
                self._emit(task, status="blocked", error_code=decision.code, started=started)
                continue

            store.begin(task, now)
            if not store.merge_and_write(client):
                report.skipped += 1
                self._emit(task, status="skipped", error_code="claim_lost", started=started)
                continue

            connector = self.connectors.get(task["connector"])
            if connector is None:
                store.finish(
                    key,
                    status="blocked",
                    summary="connector unavailable",
                    error_code="connector_unavailable",
                    retryable=False,
                    now=now,
                )
                store.merge_and_write(client)
                report.blocked += 1
                self._emit(task, status="blocked", error_code="connector_unavailable", started=started)
                continue

            try:
                result = connector.execute(task["operation"], task.get("params") or {})
                safe_result = sanitize_object(result, [self.settings.github_token])
                summary = str(safe_result.get("summary", "")) if isinstance(safe_result, dict) else str(safe_result)
                store.finish(
                    key,
                    status="succeeded",
                    summary=summary,
                    error_code=None,
                    retryable=False,
                    now=now,
                )
                if store.merge_and_write(client):
                    report.succeeded += 1
                    self.last_success_at = now.isoformat()
                    self._emit(task, status="succeeded", error_code=None, started=started)
                else:
                    report.failed += 1
                    self._emit(task, status="failed", error_code="terminal_claim_lost", started=started)
            except Exception as exc:
                store.finish(
                    key,
                    status="failed",
                    summary=redact_text(str(exc), [self.settings.github_token]),
                    error_code="connector_error",
                    retryable=False,
                    now=now,
                )
                store.merge_and_write(client)
                report.failed += 1
                self._emit(task, status="failed", error_code="connector_error", started=started)

        return report
