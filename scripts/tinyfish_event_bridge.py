#!/usr/bin/env python3
"""Reconcile persisted TinyFish Agent runs and route meaningful terminal events once."""
from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from scripts import tinyfish_senses as senses

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "state" / "tinyfish-runs.json"
FROM_TINYFISH = ROOT / "messages" / "from-tinyfish.md"
ACTION = ROOT / "messages" / "user-action-required.md"
ROUTES = {
    "chatgpt": ROOT / "messages" / "shared-inbox.md",
    "grok": ROOT / "messages" / "chatgpt-to-grok.md",
    "gemini": ROOT / "messages" / "inbox-gemini.md",
    "meta": ROOT / "messages" / "inbox-meta.md",
}
ACTIVE = {"running", "retryable"}
TERMINAL = {"done", "failed", "blocked"}
RUN_STATUS_URL = "https://agent.tinyfish.ai/v1/runs/{run_id}"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def event_key(task_id: str, run_id: str, status: str) -> str:
    raw = f"{task_id}\x1f{run_id}\x1f{status}".encode()
    return hashlib.sha256(raw).hexdigest()[:24]


def route_target(requested_by: str) -> Path:
    try:
        return ROUTES[requested_by.lower()]
    except KeyError as exc:
        raise ValueError(f"unsupported requester: {requested_by}") from exc


def _status(remote_status_value: str, current: str) -> str:
    value = remote_status_value.upper()
    if value in {"COMPLETED", "COMPLETE", "DONE"}: return "done"
    if value in {"FAILED", "CANCELLED", "CANCELED"}: return "failed"
    if value in {"RUNNING", "QUEUED", "STARTED", "PENDING", "IN_PROGRESS"}: return "running"
    return current if current in ACTIVE | TERMINAL else "running"


def normalize_event(record: dict, remote: dict) -> dict:
    status = _status(str(remote.get("status", "unknown")), str(record.get("status", "running")))
    result = remote.get("result")
    error = remote.get("error")
    blocker = ""
    next_action = ""
    if status == "failed":
        blocker = json.dumps(error, ensure_ascii=False, default=str)[:500] if error else "TinyFish run failed"
        next_action = "Review failure evidence before retrying."
    return {
        "task_id": str(record.get("task_id", "")),
        "run_id": str(record.get("run_id", "")),
        "requested_by": str(record.get("requested_by", "")),
        "mode": str(record.get("mode", "browser")),
        "status": status,
        "evidence": "messages/from-tinyfish.md" if status in TERMINAL else "",
        "result": result,
        "blocker": blocker,
        "next_action": next_action,
    }


def _event_block(event: dict) -> str:
    lines = [
        "\n---",
        f"event_key: {event_key(event['task_id'], event['run_id'], event['status'])}",
        f"task_id: {event['task_id']}",
        f"run_id: {event['run_id']}",
        "from: tinyfish-event-bridge",
        f"to: {event['requested_by']}",
        f"requested_by: {event['requested_by']}",
        f"mode: {event['mode']}",
        f"status: {event['status']}",
        f"created_at: {now()}",
        "---",
        f"evidence: {event.get('evidence', '')}",
    ]
    if event.get("blocker"): lines.append(f"blocker: {event['blocker']}")
    if event.get("next_action"): lines.append(f"next_action: {event['next_action']}")
    return "\n".join(lines) + "\n"


def route_event(event: dict, ledger: dict) -> bool:
    if event.get("status") not in TERMINAL:
        return False
    target = route_target(str(event.get("requested_by", "")))
    task_id = str(event.get("task_id", ""))
    record = ledger.get(task_id)
    if not isinstance(record, dict):
        raise ValueError(f"missing ledger record: {task_id}")
    key = event_key(task_id, str(event.get("run_id", "")), str(event.get("status", "")))
    routed = record.setdefault("routed_event_keys", [])
    if key in routed:
        return False
    text = target.read_text(encoding="utf-8") if target.exists() else ""
    target.write_text(text + _event_block(event), encoding="utf-8")
    routed.append(key)
    record["updated_at"] = now()
    return True


def remote_status(run_id: str, api_key: str) -> dict:
    req = urllib.request.Request(RUN_STATUS_URL.format(run_id=run_id), headers={"X-API-Key": api_key, "User-Agent": "cerniva-desk-tinyfish/3"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode())


def reconcile_record(record: dict, api_key: str) -> dict:
    updated = dict(record)
    run_id = str(updated.get("run_id", ""))
    if not run_id:
        updated.update({"status": "blocked", "reason_code": "missing-run-id", "last_error": "missing persisted TinyFish run_id", "updated_at": now()})
        return updated
    try:
        remote = remote_status(run_id, api_key)
        event = normalize_event(updated, remote)
        updated["status"] = event["status"]
        updated["updated_at"] = now()
        updated["last_error"] = event.get("blocker", "")
        updated["remote_result"] = remote.get("result")
        updated.pop("reason_code", None)
        return updated
    except urllib.error.HTTPError as exc:
        reason_code, reason = senses.classify_http_status(exc.code)
        updated.update({"status": "retryable" if reason_code == "transient" else "blocked", "reason_code": reason_code, "last_error": reason, "updated_at": now()})
        return updated
    except Exception as exc:
        updated.update({"status": "retryable", "reason_code": "transient", "last_error": str(exc)[:200], "updated_at": now()})
        return updated


def append_terminal_evidence(record: dict) -> None:
    block = {"run_id": record.get("run_id", ""), "result": record.get("remote_result"), "error": record.get("last_error", "")}
    task = {"id": record.get("task_id", ""), "requested_by": record.get("requested_by", "chatgpt"), "mode": record.get("mode", "browser")}
    senses.append_result(task, str(record.get("status", "failed")), block)


def main() -> int:
    key = os.environ.get("TINYFISH_API_KEY", "").strip()
    if not key:
        senses.append_action_once("TinyFish", "missing-secret", "TINYFISH_API_KEY missing; event reconciliation skipped.")
        return 0
    ledger = senses.load_ledger(RUNS)
    changed = False
    for task_id, record in list(ledger.items()):
        if not isinstance(record, dict) or record.get("status") not in ACTIVE:
            continue
        before = dict(record)
        updated = reconcile_record(record, key)
        updated.setdefault("routed_event_keys", list(record.get("routed_event_keys", [])))
        ledger[task_id] = updated
        changed = changed or updated != before
        reason_code = updated.get("reason_code")
        if updated.get("status") == "blocked" and reason_code in {"api-permission", "credits-plan"}:
            senses.append_action_once("TinyFish", str(reason_code), str(updated.get("last_error", reason_code)))
        if updated.get("status") in TERMINAL and before.get("status") not in TERMINAL:
            append_terminal_evidence(updated)
            event = normalize_event(updated, {"status": updated["status"], "result": updated.get("remote_result"), "error": updated.get("last_error")})
            changed = route_event(event, ledger) or changed
    if changed:
        senses.save_ledger(ledger, RUNS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
