#!/usr/bin/env python3
"""Grok <-> ChatGPT handoff ledger (state/handoffs.json); actors include gemini, claude, perplexity, deepseek.

Anything one side cannot do becomes a handoff item for the other.
Lifecycle: open -> claimed -> done (with SHA) -> merged (verified by the side
that handed off). ``overdue`` lists open items older than 2 h for the auditor.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "state" / "handoffs.json"
ACTORS = {"grok", "chatgpt", "auditor", "gemini", "claude", "perplexity", "deepseek", "furkan",
          "backup-supervisor", "automation-runner", "research-learner", "agents-reporter"}
STATUSES = ("open", "claimed", "done", "merged")
NEXT = {"claim": ("open", "claimed"), "done": ("claimed", "done"), "merge": ("done", "merged")}
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
ESCALATE_AFTER = timedelta(hours=2)
REQUIRED = ("id", "from", "to", "task", "reason_cannot_do", "evidence", "status", "created_at", "updated_at")


class HandoffError(ValueError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load(path: Path = DEFAULT_PATH) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "items": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    validate(data)
    return data


def save(data: dict[str, Any], path: Path = DEFAULT_PATH) -> None:
    validate(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp.write("\n")
    os.replace(tmp.name, path)
    if json.loads(path.read_text(encoding="utf-8")) != data:
        raise HandoffError("read-back mismatch")


def validate(data: dict[str, Any]) -> int:
    if data.get("schema_version") != 1 or not isinstance(data.get("items"), list):
        raise HandoffError("invalid handoff document")
    seen = set()
    for item in data["items"]:
        missing = [k for k in REQUIRED if not item.get(k)]
        if missing:
            raise HandoffError(f"{item.get('id')}: missing {','.join(missing)}")
        if item["id"] in seen:
            raise HandoffError(f"duplicate id {item['id']}")
        seen.add(item["id"])
        if item["from"] not in ACTORS or item["to"] not in ACTORS or item["from"] == item["to"]:
            raise HandoffError(f"{item['id']}: invalid from/to")
        if item["status"] not in STATUSES:
            raise HandoffError(f"{item['id']}: invalid status")
        if item["status"] in ("done", "merged") and not SHA_RE.match(str(item.get("done_sha") or "")):
            raise HandoffError(f"{item['id']}: done/merged needs done_sha")
    return len(seen)


def _find(data: dict[str, Any], item_id: str) -> dict[str, Any]:
    for item in data["items"]:
        if item["id"] == item_id:
            return item
    raise HandoffError(f"unknown id {item_id}")


def add(data, *, item_id, sender, receiver, task, reason, evidence, at=None):
    if any(i["id"] == item_id for i in data["items"]):
        raise HandoffError(f"duplicate id {item_id}")
    stamp = at or now()
    item = {"id": item_id, "from": sender, "to": receiver, "task": task, "reason_cannot_do": reason,
            "evidence": evidence, "status": "open", "created_at": stamp, "updated_at": stamp}
    data["items"].append(item)
    validate(data)
    return item


def transition(data, item_id, action, *, actor, sha=None, note=None, at=None):
    item = _find(data, item_id)
    before, after = NEXT[action]
    if item["status"] != before:
        raise HandoffError(f"{item_id}: {action} needs status {before}, is {item['status']}")
    if action in ("claim", "done") and actor != item["to"]:
        raise HandoffError(f"{item_id}: only {item['to']} may {action}")
    if action == "merge" and actor != item["from"]:
        raise HandoffError(f"{item_id}: only {item['from']} verifies and merges")
    if action == "done":
        if not sha or not SHA_RE.match(sha):
            raise HandoffError("done requires a commit SHA")
        item["done_sha"] = sha
    stamp = at or now()
    item["status"] = after
    item[f"{after}_at"] = stamp
    item["updated_at"] = stamp
    if note:
        item.setdefault("notes", []).append(f"{stamp} {actor}: {note}")
    validate(data)
    return item


def overdue(data, *, at: datetime | None = None) -> list[dict[str, Any]]:
    current = at or datetime.now(timezone.utc)
    return [i for i in data["items"] if i["status"] == "open"
            and current - datetime.fromisoformat(i["created_at"]) > ESCALATE_AFTER]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--file", type=Path, default=DEFAULT_PATH)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    for flag in ("id", "from", "to", "task", "reason", "evidence"):
        a.add_argument("--" + flag, required=True)
    for cmd in ("claim", "done", "merge"):
        c = sub.add_parser(cmd)
        c.add_argument("id")
        c.add_argument("--actor", required=True, choices=sorted(ACTORS))
        c.add_argument("--note")
        if cmd == "done":
            c.add_argument("--sha", required=True)
    sub.add_parser("validate")
    sub.add_parser("overdue")
    args = p.parse_args(argv)
    data = load(args.file)
    if args.cmd == "validate":
        print(json.dumps({"valid": True, "items": validate(data)}))
        return 0
    if args.cmd == "overdue":
        items = overdue(data)
        print(json.dumps([i["id"] for i in items]))
        return 1 if items else 0
    if args.cmd == "add":
        result = add(data, item_id=args.id, sender=getattr(args, "from"), receiver=args.to,
                     task=args.task, reason=args.reason, evidence=args.evidence)
    else:
        result = transition(data, args.id, args.cmd, actor=args.actor,
                            sha=getattr(args, "sha", None), note=args.note)
    save(data, args.file)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HandoffError as exc:
        print(f"handoff error: {exc}")
        raise SystemExit(2)
