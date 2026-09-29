#!/usr/bin/env python3
"""Normalize desk-notify health metadata to the live workflow and source messages."""
from __future__ import annotations

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


def collect_active_ids(messages_dir: Path = MESSAGES_DIR) -> set[str]:
    ids: set[str] = set()
    if not messages_dir.exists():
        return ids
    for path in messages_dir.glob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        ids.update(ID_RE.findall(text))
        ids.update(RPT_RE.findall(text))
    return ids


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
    normalized = normalize_health(health, ledger, collect_active_ids())
    HEALTH_PATH.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
