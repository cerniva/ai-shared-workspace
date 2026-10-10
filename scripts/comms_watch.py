#!/usr/bin/env python3
"""Comms watcher: unacked new handoffs and unread desk messages, no API key.

(a) handoffs with status open, no claimed_at/ack, older than NEW_HANDOFF_MINUTES
    and younger than handoff.ESCALATE_AFTER (>2h is agents-reporter/handoff-audit
    territory and is not repeated here);
(b) unread desk_bridge INBOX_WATCH_CHANNELS rows older than
    desk_bridge.INBOX_UNREAD_ALARM_MINUTES.
Messages created before WATCH_SINCE (9 Ekim backlog, closed as superseded in
state/superseded_messages.json) are never alerted.

Output: {"alerts": [{id, owner, kind, age_min}], "active": [...], "dispatches": [...]}.
"alerts" holds only ids not alerted before (state/comms_watch.json); "active"
holds every currently matching item so CI can keep one issue open/closed;
"dispatches" holds repository_dispatch bodies (event_type team-work), sent once
per handoff id. On repository_dispatch (main-merged / team-pr-opened; GITHUB_TOKEN
merges/pushes start no workflows) client_payload.handoff_id is checked first
and reported under "priority".

ChatGPT triggers (event read from GITHUB_EVENT_NAME / GITHUB_EVENT_PATH):
- push to a chatgpt/* branch -> team-work {source: chatgpt, branch, sha}, once per
  branch+sha (state key "chatgpt_branches"). chatgpt/* branches are only read, never modified.
- new message block appended to messages/chatgpt-to-grok.md -> team-work
  {source: chatgpt, message_id (or line_hash), path}, once per message key (state key
  "chatgpt_messages"). The first run without that key only records a baseline so the
  existing backlog is not dispatched. Items with source backlog-migration are never dispatched.
"""
from __future__ import annotations

import argparse
import hashlib
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
NO_DISPATCH_SOURCES = frozenset({"backlog-migration"})  # alerted, never auto-dispatched
# Grok Bot onayı 2026-10-10: older messages are closed as superseded; watch only new ones.
WATCH_SINCE = datetime.fromisoformat("2026-10-09T00:00:00+03:00")
CHATGPT_SOURCE = "chatgpt"
CHATGPT_BRANCH_PREFIX = "chatgpt/"
CHATGPT_MESSAGES_REL = "messages/chatgpt-to-grok.md"
CHATGPT_MESSAGES_PATH = ROOT / CHATGPT_MESSAGES_REL
SKIP_SOURCES = NO_DISPATCH_SOURCES
# Telegram /gorev handoffs (TG-*) are dispatched by telegram_bot itself; never twice.
SELF_DISPATCHED_PREFIXES = ("TG-",)


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
        alert = {"id": item["id"], "owner": item.get("to", "unknown"), "kind": "handoff_unacked",
                 "age_min": _age_min(created, now), "task": item.get("task", "")}
        if item.get("source"):
            alert["source"] = item["source"]
        out.append(alert)
    return out


def _channel_owner(channel: str) -> str:
    spec = desk_bridge.CHANNELS.get(channel)
    return spec[2] if spec else "team"


def _before_watch_since(created_at: Any) -> bool:
    try:
        created = datetime.fromisoformat(str(created_at))
    except ValueError:
        return False
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone(timedelta(hours=3)))
    return created < WATCH_SINCE


def inbox_alerts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        if row.get("id") in SKIP_IDS or _before_watch_since(row.get("created_at")):
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
        if a.get("kind") != "handoff_unacked" or a["id"] in dispatched or a.get("source") in NO_DISPATCH_SOURCES \
                or str(a["id"]).startswith(SELF_DISPATCHED_PREFIXES):
            continue
        out.append({"event_type": DISPATCH_EVENT,
                    "client_payload": {"handoff_id": a["id"], "task": a.get("task", ""), "source": "comms-watch"}})
    return out


def priority_handoff_id(event_path: str | os.PathLike | None) -> str | None:
    """handoff_id from a repository_dispatch (main-merged / team-pr-opened) event payload."""
    if not event_path:
        return None
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    payload = event.get("client_payload") if isinstance(event, dict) else None
    hid = payload.get("handoff_id") if isinstance(payload, dict) else None
    return str(hid).strip() or None if hid else None


def priority_status(data: dict[str, Any], hid: str | None) -> dict[str, Any] | None:
    if not hid:
        return None
    for item in data.get("items", []):
        if item.get("id") == hid:
            return {"id": hid, "found": True, "status": item.get("status"), "owner": item.get("to"),
                    "acked": bool(any(item.get(k) for k in ACK_KEYS) or item.get("notes"))}
    return {"id": hid, "found": False}


def chatgpt_branch_from_event(event_name: str | None, event: dict[str, Any] | None) -> dict[str, str] | None:
    """{branch, sha} for a push to refs/heads/chatgpt/*; None otherwise (deletes ignored)."""
    if event_name != "push" or not isinstance(event, dict):
        return None
    ref = str(event.get("ref") or "")
    if not ref.startswith("refs/heads/" + CHATGPT_BRANCH_PREFIX) or event.get("deleted"):
        return None
    sha = str(event.get("after") or "").strip()
    if not sha or set(sha) == {"0"}:
        return None
    head = event.get("head_commit") if isinstance(event.get("head_commit"), dict) else {}
    message = str(head.get("message") or "")
    if any(f"source: {src}" in message or f"source:{src}" in message for src in SKIP_SOURCES):
        return None
    return {"branch": ref[len("refs/heads/"):], "sha": sha}


def chatgpt_branch_dispatch(info: dict[str, str] | None, done: dict[str, str]) -> list[dict[str, Any]]:
    if not info:
        return []
    key = f"{info['branch']}@{info['sha']}"
    if key in done:
        return []
    return [{"event_type": DISPATCH_EVENT, "dispatch_key": key,
             "client_payload": {"source": CHATGPT_SOURCE, "branch": info["branch"], "sha": info["sha"]}}]


def parse_chatgpt_messages(text: str) -> list[dict[str, str]]:
    """Message blocks of the append-only desk file: each starts at an `id:` header line
    (or any `key: value` header after a `---` line) and runs to the next `---`-delimited header."""
    lines = text.splitlines()
    starts = [i for i, line in enumerate(lines) if line.strip().startswith("id:")
              and (i == 0 or lines[i - 1].strip() in ("---", ""))]
    out = []
    for n, start in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        block = lines[start:end]
        while block and block[-1].strip() in ("---", ""):
            block = block[:-1]
        header: dict[str, str] = {}
        for line in block:
            if line.strip() == "---":
                break
            if ":" in line:
                k, v = line.split(":", 1)
                header[k.strip()] = v.strip()
        body = "\n".join(block)
        msg_id = header.get("id", "")
        out.append({"message_id": msg_id, "line_hash": hashlib.sha256(body.encode("utf-8")).hexdigest()[:16],
                    "source": header.get("source", ""), "key": msg_id or "hash:" + hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]})
    return out


def chatgpt_message_dispatches(messages: list[dict[str, str]], done: dict[str, str],
                               path: str = CHATGPT_MESSAGES_REL) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for m in messages:
        if m["key"] in done or m["key"] in seen or m.get("source") in SKIP_SOURCES:
            continue
        seen.add(m["key"])
        payload = {"source": CHATGPT_SOURCE, "path": path}
        if m["message_id"]:
            payload["message_id"] = m["message_id"]
        else:
            payload["line_hash"] = m["line_hash"]
        out.append({"event_type": DISPATCH_EVENT, "dispatch_key": m["key"], "client_payload": payload})
    return out


def read_event(event_path: str | os.PathLike | None) -> dict[str, Any] | None:
    if not event_path:
        return None
    try:
        event = json.loads(Path(event_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return event if isinstance(event, dict) else None


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
        write_state: bool = True, priority_id: str | None = None,
        event_name: str | None = None, event: dict[str, Any] | None = None,
        chatgpt_messages_path: Path = CHATGPT_MESSAGES_PATH) -> dict[str, Any]:
    current = now or datetime.now(timezone.utc)
    data = handoff.load(handoffs_path)
    rows = desk_bridge.unread_message_rows() if inbox_rows is None else inbox_rows
    active = handoff_alerts(data, now=current) + inbox_alerts(rows)
    if priority_id:  # repository_dispatch payload handoff is checked/reported first
        active.sort(key=lambda a: a["id"] != priority_id)
    state = load_state(state_path)
    alerted: dict[str, str] = state["alerted"]
    stamp = current.replace(microsecond=0).isoformat()
    fresh = [a for a in active if a["id"] not in alerted]
    for a in fresh:
        alerted[a["id"]] = stamp
    dispatches = dispatch_payloads(fresh, state["dispatched"])
    for d in dispatches:
        state["dispatched"][d["client_payload"]["handoff_id"]] = stamp
    branches = state.setdefault("chatgpt_branches", {})
    if not isinstance(branches, dict):
        branches = state["chatgpt_branches"] = {}
    branch_d = chatgpt_branch_dispatch(chatgpt_branch_from_event(event_name, event), branches)
    for d in branch_d:
        branches[d["dispatch_key"]] = stamp
    # On chatgpt/* pushes the Actions cache is branch-scoped, so message dedupe stays on main runs.
    on_chatgpt_branch = event_name == "push" and isinstance(event, dict) and \
        str(event.get("ref") or "").startswith("refs/heads/" + CHATGPT_BRANCH_PREFIX)
    msg_d: list[dict[str, Any]] = []
    if not on_chatgpt_branch:
        try:
            messages = parse_chatgpt_messages(chatgpt_messages_path.read_text(encoding="utf-8"))
        except OSError:
            messages = []
        baseline = not isinstance(state.get("chatgpt_messages"), dict)
        seen_msgs = state["chatgpt_messages"] = {} if baseline else state["chatgpt_messages"]
        msg_d = [] if baseline else chatgpt_message_dispatches(messages, seen_msgs)
        for m in messages:
            seen_msgs.setdefault(m["key"], stamp)
    dispatches = dispatches + branch_d + msg_d
    state["last_run_at"] = stamp
    if write_state:
        save_state(state, state_path)
    return {"alerts": fresh, "active": active, "dispatches": dispatches,
            "priority": priority_status(data, priority_id)}


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
    p.add_argument("--event-path", default=os.environ.get("GITHUB_EVENT_PATH"),
                   help="GitHub event JSON; client_payload.handoff_id is checked first")
    p.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME"))
    args = p.parse_args(argv)
    result = run(handoffs_path=args.handoffs, state_path=args.state, write_state=not args.no_write,
                 priority_id=priority_handoff_id(args.event_path),
                 event_name=args.event_name, event=read_event(args.event_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if args.telegram:
        notify_telegram(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
