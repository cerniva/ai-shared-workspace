#!/usr/bin/env python3
"""Append-only, idempotent task-stage event ledger (not a chat notification transport)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "state" / "task_events.json"
STAGES = {
    "task_started", "research_started", "source_found", "source_read",
    "source_evaluated", "information_shared", "seen", "reviewed", "used",
    "not_used", "work_started", "blocker_reported", "help_requested",
    "fix_started", "test_passed", "test_failed", "learning_saved",
    "handoff", "task_completed",
}
STATUSES = {
    "in_progress", "done", "blocked", "seen", "reviewed", "used",
    "not_used", "useful", "not_useful", "needs_more", "passed", "failed",
}
ACTORS = {"chatgpt", "grok", "gemini", "meta", "human", "worker"}


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def read_ledger(path: Path = LEDGER) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {"schema_version": 1, "events": []}
    if not isinstance(data, dict) or not isinstance(data.get("events"), list):
        raise ValueError("invalid task event ledger shape")
    return data


def write_ledger(data: dict, path: Path = LEDGER) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def log_event(*, task_id: str, stage: str, actor: str, status: str,
              evidence: str = "", next_action: str = "", event_id: str | None = None,
              source_title: str = "", source_url: str = "", source_accessed: str = "",
              reason: str = "", path: Path = LEDGER) -> tuple[dict, bool]:
    task_id, stage, actor, status = task_id.strip(), stage.strip(), actor.strip().lower(), status.strip().lower()
    if not task_id:
        raise ValueError("task_id is required")
    if stage not in STAGES:
        raise ValueError(f"invalid stage: {stage}")
    if actor not in ACTORS:
        raise ValueError(f"invalid actor: {actor}")
    if status not in STATUSES:
        raise ValueError(f"invalid status: {status}")
    if stage == "source_found" and not (source_title.strip() and source_url.strip()):
        raise ValueError("source_found requires source_title and source_url")
    if stage == "source_evaluated" and not reason.strip():
        raise ValueError("source_evaluated requires a usefulness reason")
    eid = (event_id or str(uuid.uuid4())).strip()
    if not eid:
        raise ValueError("event_id cannot be empty")
    event = {
        "event_id": eid,
        "task_id": task_id,
        "stage": stage,
        "actor": actor,
        "status": status,
        "at": now_iso(),
        "evidence": evidence.strip(),
        "next_action": next_action.strip(),
        "reason": reason.strip(),
    }
    if source_title.strip() or source_url.strip() or source_accessed.strip():
        event["source"] = {
            "title": source_title.strip(),
            "url": source_url.strip(),
            "accessed_at": source_accessed.strip(),
        }
    data = read_ledger(path)
    old = next((item for item in data["events"] if item.get("event_id") == eid), None)
    if old:
        comparable = {k: v for k, v in event.items() if k != "at"}
        old_comparable = {k: v for k, v in old.items() if k != "at"}
        if comparable != old_comparable:
            raise ValueError(f"event_id already used with different payload: {eid}")
        return old, False
    data["events"].append(event)
    write_ledger(data, path)
    return event, True


def list_events(task_id: str | None = None, path: Path = LEDGER) -> list[dict]:
    events = read_ledger(path)["events"]
    return [event for event in events if not task_id or event.get("task_id") == task_id]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    log = sub.add_parser("log", help="append a task-stage event")
    log.add_argument("--task-id", required=True)
    log.add_argument("--stage", required=True, choices=sorted(STAGES))
    log.add_argument("--actor", required=True, choices=sorted(ACTORS))
    log.add_argument("--status", required=True, choices=sorted(STATUSES))
    log.add_argument("--evidence", default="")
    log.add_argument("--next-action", default="")
    log.add_argument("--event-id", help="stable ID for safe retries")
    log.add_argument("--source-title", default="")
    log.add_argument("--source-url", default="")
    log.add_argument("--source-accessed", default="")
    log.add_argument("--reason", default="")
    listing = sub.add_parser("list", help="show recorded events")
    listing.add_argument("--task-id")
    args = parser.parse_args()
    if args.command == "log":
        event, created = log_event(
            task_id=args.task_id, stage=args.stage, actor=args.actor, status=args.status,
            evidence=args.evidence, next_action=args.next_action, event_id=args.event_id,
            source_title=args.source_title, source_url=args.source_url,
            source_accessed=args.source_accessed, reason=args.reason,
        )
        print(json.dumps({"created": created, "event": event}, ensure_ascii=False))
    else:
        print(json.dumps(list_events(args.task_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
