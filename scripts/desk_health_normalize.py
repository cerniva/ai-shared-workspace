#!/usr/bin/env python3
"""Normalize desk-notify health metadata to the live workflow and source messages."""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEALTH_PATH = ROOT / "state" / "desk_notify_health.json"
DELIVERY_PATH = ROOT / "state" / "message_delivery.json"
MESSAGES_DIR = ROOT / "messages"
STATUSES = ("pending", "seen", "answered", "delayed")
ID_RE = re.compile(r"(?m)^id:\s*(\S+)\s*$")
RPT_RE = re.compile(r"(?m)^##\s+(RPT-\S+)\s*$")
SPLIT_RE = re.compile(r"(?m)^---\s*$")
TERMINAL_SOURCE_STATUSES = {"done", "blocked", "superseded"}


def collect_active_ids(messages_dir: Path = MESSAGES_DIR) -> set[str]:
    ids: set[str] = set()
    if not messages_dir.exists():
        return ids
    for path in messages_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        ids.update(ID_RE.findall(text))
        ids.update(RPT_RE.findall(text))
    return ids


def collect_message_source_statuses(messages_dir: Path = MESSAGES_DIR) -> dict[str, str]:
    """Return the latest explicit source status for file-desk message records."""
    found: dict[str, str] = {}
    if not messages_dir.exists():
        return found
    for path in messages_dir.glob("*.md"):
        parts = SPLIT_RE.split(path.read_text(encoding="utf-8", errors="replace"))
        i = 1
        while i + 1 < len(parts):
            fields: dict[str, str] = {}
            for line in parts[i].strip().splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                fields[key.strip().lower()] = value.strip()
            mid = fields.get("id")
            status = fields.get("status")
            if mid and status:
                found[mid] = status.lower()
            i += 2
    return found


def reconcile_terminal_delivery(ledger: dict, source_statuses: dict[str, str], now: dt.datetime | None = None) -> int:
    """Clear false delayed/pending delivery states after the source message is terminal."""
    now = now or dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))
    stamp = now.isoformat(timespec="seconds")
    changed = 0
    for mid, source_status in source_statuses.items():
        if source_status not in TERMINAL_SOURCE_STATUSES:
            continue
        entry = (ledger.get("messages") or {}).get(mid)
        if not isinstance(entry, dict) or entry.get("status") == "answered":
            continue
        entry["status"] = "answered"
        entry["message_status"] = source_status
        entry["needs_reply"] = False
        entry["updated_at"] = stamp
        entry.setdefault("answered_at", stamp)
        transitions = entry.setdefault("transitions_emitted", [])
        if "answered" not in transitions:
            transitions.append("answered")
        changed += 1
    return changed


def normalize_health(health: dict, ledger: dict, active_ids: set[str]) -> dict:
    historical = {status: 0 for status in STATUSES}
    active = {status: 0 for status in STATUSES}
    for mid, entry in (ledger.get("messages") or {}).items():
        status = str((entry or {}).get("status") or "")
        if status not in historical:
            continue
        historical[status] += 1
        if mid in active_ids:
            active[status] += 1

    out = dict(health)
    out["historical_counts"] = historical
    out["counts"] = active
    out["counts_scope"] = "active message/report source IDs only; historical_counts preserves full ledger totals"
    out["active_source_id_count"] = len(active_ids)
    out["schedule"] = "0 * * * *"
    out["retry"] = (
        "workflow job fails closed; next hourly schedule (0 * * * *) or workflow_dispatch reruns reconcile. "
        "Unsaved transitions stay absent and are retried. Emitted event keys are not repeated."
    )
    out["normalized_by"] = "scripts/desk_health_normalize.py"
    return out


def main() -> int:
    health = json.loads(HEALTH_PATH.read_text(encoding="utf-8"))
    ledger = json.loads(DELIVERY_PATH.read_text(encoding="utf-8"))
    terminal_reconciled = reconcile_terminal_delivery(ledger, collect_message_source_statuses())
    if terminal_reconciled:
        DELIVERY_PATH.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    normalized = normalize_health(health, ledger, collect_active_ids())
    normalized["terminal_source_reconciled"] = terminal_reconciled
    HEALTH_PATH.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
