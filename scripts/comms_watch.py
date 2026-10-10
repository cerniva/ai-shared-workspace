#!/usr/bin/env python3
"""Comms watcher: unacked new handoffs and unread desk messages, no API key.

(a) handoffs with status open, no claimed_at/ack, older than NEW_HANDOFF_MINUTES
    and younger than handoff.ESCALATE_AFTER (>2h is agents-reporter/handoff-audit
    territory and is not repeated here);
(b) unread desk_bridge INBOX_WATCH_CHANNELS rows older than
    desk_bridge.INBOX_UNREAD_ALARM_MINUTES.

Output: {"alerts": [{id, owner, kind, age_min}], "active": [...], "dispatches": [...]}.
"alerts" holds only ids not alerted before (state/comms_watch.json); "active"
holds every currently matching item so CI can keep one issue open/closed;
"dispatches" holds repository_dispatch bodies (event_type team-work), sent once
per handoff id.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import desk_bridge, handoff  # noqa: E402

STATE_PATH = ROOT / "state" / "comms_watch.json"
NEW_HANDOFF_MINUTES = 15
SKIP_IDS = frozenset({"HO-20261009-03", "HO-20261009-08"})  # Furkan already knows
ACK_KEYS = ("claimed_at", "acked_at", "ack", "ack_at")
DISPATCH_EVENT = "team-work"


def _age_min(created: datetime, now: datetime) -> int:
    return int((now - created).total_seconds() // 60)


def handoff_alerts(data: dict[str, Any], *, now: datetime) -> list[dict[str, Any]]:
    out = []
    for item in data.get("items", []):
        if item.get("id") in SKIP_IDS or item.get("status") != "open":
            continue
        if any(item.get(k) for k in ACK_KEYS) or item.get("notes"):
            continue
        try:
            created = datetime.fromisoformat(str(item["created_at"]))
        except (KeyError, ValueError):
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        age = now - created
        if age < timedelta(minutes=NEW_HANDOFF_MINUTES) or age > handoff.ESCALATE_AFTER:
            continue
        out.append({"id": item["id"], "owner": item.get("to", "unknown"), "kind": "handoff_unacked",
                    "age_min": _age_min(created, now), "task": item.get("task", "")})
    return out


def _channel_owner(channel: str) -> str:
    spec = desk_bridge.CHANNELS.get(channel)
    return spec[2] if spec else "team"


def inbox_alerts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if row.get("id") in SKIP_IDS:
            continue
        age_min = int(round(float(row.get("age_hours", 0)) * 60))
        if age_min < desk_bridge.INBOX_UNREAD_ALARM_MINUTES:
            continue
        out.append({"id": row["id"], "owner": _channel_owner(row["channel"]), "kind": "inbox_unread",
                    "age_min": age_min, "channel": row["channel"]})
    return out


def dispatch_payloads(alerts: list[dict[str, Any]], dispatched: dict[str, str]) -> list[dict[str, Any]]:
    """repository_dispatch bodies for new handoff alerts not dispatched before."""
    out = []
    for a in alerts:
        if a.get("kind") != "handoff_unacked" or a["id"] in dispatched:
            continue
        out.append({"event_type": DISPATCH_EVENT,
                    "client_payload": {"handoff_id": a["id"], "task": a.get("task", ""), "source": "comms-watch"}})
    return out


def load_state(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "alerted": {}, "dispatched": {}}
    if not isinstance(value, dict) or not isinstance(value.get("alerted"), dict):
        return {"schema_version": 1, "alerted": {}, "dispatched": {}}
    if not isinstance(value.get("dispatched"), dict):
        value["dispatched"] = {}
    return value


def save_state(state: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def run(*, handoffs_path: Path = handoff.DEFAULT_PATH, state_path: Path = STATE_PATH,
        now: datetime | None = None, inbox_rows: list[dict[str, Any]] | None = None,
        write_state: bool = True) -> dict[str, Any]:
    current = now or datetime.now(timezone.utc)
    data = handoff.load(handoffs_path)
    rows = desk_bridge.unread_message_rows() if inbox_rows is None else inbox_rows
    active = handoff_alerts(data, now=current) + inbox_alerts(rows)
    state = load_state(state_path)
    alerted: dict[str, str] = state["alerted"]
    stamp = current.replace(microsecond=0).isoformat()
    fresh = [a for a in active if a["id"] not in alerted]
    for a in fresh:
        alerted[a["id"]] = stamp
    dispatches = dispatch_payloads(fresh, state["dispatched"])
    for d in dispatches:
        state["dispatched"][d["client_payload"]["handoff_id"]] = stamp
    state["last_run_at"] = stamp
    if write_state:
        save_state(state, state_path)
    return {"alerts": fresh, "active": active, "dispatches": dispatches}


def telegram_text(result: dict[str, Any], limit: int = 30) -> str:
    lines = [f"comms-watch: {len(result['alerts'])} yeni uyarı"]
    for a in result["alerts"][:limit]:
        lines.append(f"- {a['kind']} {a['id']} → {a['owner']} ({a['age_min']} dk)")
    if len(result["alerts"]) > limit:
        lines.append(f"... +{len(result['alerts']) - limit}")
    return "\n".join(lines)


def notify_telegram(result: dict[str, Any], *, env=None, http=None) -> bool:
    """Send-only via telegram_bot helpers; never calls getUpdates (no offset theft)."""
    values = os.environ if env is None else env
    token = values.get("TELEGRAM_BOT_TOKEN", "").strip()
    chats = [c.strip() for c in values.get("TELEGRAM_ALLOWED_CHAT_ID", "").split(",") if c.strip()]
    if not token or not chats or not result["alerts"]:
        return False
    from scripts import telegram_bot
    api = f"https://api.telegram.org/bot{token}"
    for chat in chats:
        telegram_bot._send(http or telegram_bot.default_http, api, chat, telegram_text(result))
    return True


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--handoffs", type=Path, default=handoff.DEFAULT_PATH)
    p.add_argument("--state", type=Path, default=STATE_PATH)
    p.add_argument("--no-write", action="store_true", help="do not update the dedupe state")
    p.add_argument("--telegram", action="store_true", help="send new alerts via telegram_bot helpers if token set")
    args = p.parse_args(argv)
    result = run(handoffs_path=args.handoffs, state_path=args.state, write_state=not args.no_write)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.telegram:
        notify_telegram(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
