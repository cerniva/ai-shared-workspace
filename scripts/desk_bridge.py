#!/usr/bin/env python3
"""File-desk bridge: messages, read cursors, and deduped delivery ledger.

Transport is a polled ledger (state/message_delivery.json). This is not a push
into ChatGPT or Grok chat. GitHub's notifications API cannot create a
notification, and GITHUB_TOKEN events do not start other workflows.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import FrozenSet

ROOT = Path(__file__).resolve().parents[1]

def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)

CHANNELS: dict[str, tuple[Path, str | FrozenSet[str] | None, str]] = {
    "grok-to-chatgpt": (ROOT / "messages" / "grok-to-chatgpt.md", frozenset({"grok", "grok-bot"}), "chatgpt"),
    "chatgpt-to-grok": (ROOT / "messages" / "chatgpt-to-grok.md", "chatgpt", "grok"),
    "inbox-gemini": (ROOT / "messages" / "inbox-gemini.md", None, "gemini"),
    "gemini-to-chatgpt": (ROOT / "messages" / "gemini-to-chatgpt.md", "gemini", "chatgpt"),
    "chatgpt-to-gemini": (ROOT / "messages" / "chatgpt-to-gemini.md", "chatgpt", "gemini"),
    "shared-inbox": (ROOT / "messages" / "shared-inbox.md", None, "team"),
}
VALID_STATUS = {"open", "done", "blocked", "queued"}
STALE_HOURS = 24
INBOX_WATCH_CHANNELS = (
    "chatgpt-to-grok",
    "grok-to-chatgpt",
    "chatgpt-to-gemini",
    "gemini-to-chatgpt",
    "shared-inbox",
)
INBOX_UNREAD_ALARM_MINUTES = 10
INBOX_READ_PATH = ROOT / "state" / "inbox_read.json"
DELIVERY_PATH = ROOT / "state" / "message_delivery.json"
HEALTH_PATH = ROOT / "state" / "desk_notify_health.json"
TEAM_REPORTS_PATH = ROOT / "messages" / "team-reports.md"
DELIVERY_STATUSES = ("pending", "seen", "answered", "delayed")
DELAYED_AFTER_MINUTES = 30
OPEN_LIKE = {"open", "queued", "active", "ready", "run", "in_progress"}
_SPLIT = re.compile(r"(?m)^---\s*$")
_RPT_SPLIT = re.compile(r"(?m)^## (RPT-\S+)\s*$")
PUSH_LIMIT = (
    "poll-ledger only. GitHub REST notifications API has no create endpoint "
    "(docs/en/rest/activity/notifications, checked 2026-09-27). GITHUB_TOKEN "
    "events do not start workflows except workflow_dispatch and repository_dispatch "
    "(docs/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow, "
    "checked 2026-09-27). No PAT stored. Chat push was not tested and is not claimed."
)


def now_tr() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))


def make_id(agent: str) -> str:
    n = now_tr()
    return f"MSG-{n.strftime('%Y%m%d-%H%M%S')}-{n.microsecond:06d}-{agent.replace('_','').replace(' ','')}-bridge"


def _parse_created_at(value: str) -> dt.datetime | None:
    if not value:
        return None
    text = value.strip()
    try:
        x = dt.datetime.fromisoformat(text)
    except (TypeError, ValueError):
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
            y, m, d = (int(p) for p in text.split("-"))
            return dt.datetime(y, m, d, tzinfo=dt.timezone(dt.timedelta(hours=3)))
        return None
    return x if x.tzinfo else x.replace(tzinfo=dt.timezone(dt.timedelta(hours=3)))


def _parse_blocks(text: str) -> list[dict[str, str]]:
    parts = _SPLIT.split(text)
    out: list[dict[str, str]] = []
    i = 1
    while i + 1 < len(parts):
        fields: dict[str, str] = {}
        for line in parts[i].strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()
        if "id" in fields:
            fields["body"] = parts[i + 1].strip()
            out.append(fields)
        i += 2
    return out


def parse_team_reports(text: str) -> list[dict[str, str]]:
    parts = _RPT_SPLIT.split(text)
    out: list[dict[str, str]] = []
    i = 1
    while i + 1 < len(parts):
        rid = parts[i].strip()
        body = parts[i + 1].strip()
        fields: dict[str, str] = {
            "id": rid,
            "body": body,
            "from": "",
            "to": "team",
            "status": "",
            "in_reply_to": "none",
            "created_at": "",
        }
        for raw in body.splitlines():
            line = raw.strip()
            if line.startswith("- "):
                line = line[2:].strip()
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key in {"from", "status", "project", "in_reply_to"}:
                fields[key] = value
        match = re.match(r"RPT-(\d{8})-(\d{4})", rid)
        if match:
            day, hm = match.group(1), match.group(2)
            fields["created_at"] = f"{day[:4]}-{day[4:6]}-{day[6:8]}T{hm[:2]}:{hm[2:]}:00+03:00"
        if not fields["from"]:
            fields["from"] = "unknown"
        out.append(fields)
        i += 2
    return out


def _allowed(expected: str | FrozenSet[str] | None) -> set[str] | None:
    return None if expected is None else ({expected} if isinstance(expected, str) else set(expected))


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _watch_map() -> dict[str, Path]:
    found = {name: spec[0] for name, spec in CHANNELS.items()}
    found["team-reports"] = TEAM_REPORTS_PATH
    return found


def _blocks_for(name: str) -> list[dict[str, str]]:
    path = _watch_map().get(name)
    if path is None or not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    if name == "team-reports":
        return parse_team_reports(text)
    return _parse_blocks(text)


def message_needs_reply(block: dict) -> bool:
    if block.get("_channel") == "team-reports" or str(block.get("id", "")).startswith("RPT-"):
        return False
    status = (block.get("status") or "").lower()
    if status in {"done", "superseded", "blocked"}:
        return False
    for line in (block.get("body") or "").splitlines():
        if not line.lower().startswith("intent:"):
            continue
        tail = line.split(":", 1)[1].lower()
        if "ask" in tail:
            return True
        if "info" in tail:
            return False
    return status in OPEN_LIKE


def _blank_parent(in_reply_to: str | None) -> bool:
    return not in_reply_to or in_reply_to.lower() in {"null", "none", ""}


def load_delivery_state() -> dict:
    try:
        value = json.loads(DELIVERY_PATH.read_text(encoding="utf-8"))
        if isinstance(value, dict) and isinstance(value.get("messages"), dict):
            value.setdefault("events", [])
            value.setdefault("event_keys", [])
            return value
    except (OSError, json.JSONDecodeError):
        pass
    return {"messages": {}, "events": [], "event_keys": []}


def save_delivery_state(state: dict) -> None:
    state.setdefault("messages", {})
    state.setdefault("events", [])
    state.setdefault("event_keys", [])
    _atomic_write(DELIVERY_PATH, json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def _notify_target(entry: dict, status: str) -> str:
    if status in {"seen", "answered"}:
        return str(entry.get("from") or "unknown")
    return str(entry.get("to") or "team")


def _record_event(state: dict, entry: dict, status: str, *, reason: str, read_by: str | None) -> bool:
    emitted = entry.setdefault("transitions_emitted", [])
    if status in emitted:
        return False
    emitted.append(status)
    key = f"{entry['id']}:{status}"
    keys = state.setdefault("event_keys", [])
    if key in keys:
        return False
    keys.append(key)
    event = {
        "key": key,
        "message_id": entry["id"],
        "transition": status,
        "notify": _notify_target(entry, status),
        "reason": reason,
        "channel": entry.get("channel"),
        "at": entry.get("updated_at"),
        "transport": "poll-ledger",
        "push": False,
    }
    if read_by:
        event["read_by"] = read_by
    state.setdefault("events", []).append(event)
    return True


def mark_delivery(
    channel: str,
    mid: str,
    status: str,
    *,
    force: bool = False,
    alert: bool = True,
    meta: dict | None = None,
    reason: str | None = None,
    read_by: str | None = None,
) -> dict:
    if status not in DELIVERY_STATUSES:
        raise ValueError(f"invalid delivery status: {status}")
    state = load_delivery_state()
    msgs = state["messages"]
    prev = msgs.get(mid) or {}
    if not force and status == "pending" and prev.get("status") == "pending":
        return prev
    if not force and prev.get("status") == "answered" and status in ("pending", "seen", "delayed"):
        return prev
    if prev.get("status") == status:
        return prev
    if prev.get("status") == "answered" and status != "answered":
        return prev
    if status == "pending" and prev.get("status") in {"seen", "delayed", "answered"}:
        return prev
    stamp = now_tr().isoformat(timespec="seconds")
    meta = meta or {}
    entry = {
        "id": mid,
        "channel": channel or prev.get("channel") or meta.get("channel") or "",
        "status": status,
        "updated_at": stamp,
        "alerted": status == "pending" or bool(prev.get("alerted")),
    }
    for field in ("from", "to", "needs_reply", "message_status", "in_reply_to", "created_at", "backfill", "seen_by"):
        if field in prev:
            entry[field] = prev[field]
        elif field in meta and meta[field] is not None:
            entry[field] = meta[field]
    if "needs_reply" not in entry:
        entry["needs_reply"] = True
    entry["transitions_emitted"] = list(prev.get("transitions_emitted") or [])
    if "pending_at" in prev:
        entry["pending_at"] = prev["pending_at"]
    if status == "pending":
        entry["pending_at"] = prev.get("pending_at") or meta.get("created_at") or stamp
        entry["alerted"] = True
    if "seen_at" in prev:
        entry["seen_at"] = prev["seen_at"]
    if status == "seen":
        entry["seen_at"] = prev.get("seen_at") or stamp
        if read_by:
            seen_by = list(entry.get("seen_by") or [])
            if read_by not in seen_by:
                seen_by.append(read_by)
            entry["seen_by"] = seen_by
    if status == "answered":
        entry["answered_at"] = prev.get("answered_at") or stamp
    if status == "delayed":
        entry["delayed_at"] = prev.get("delayed_at") or stamp
    if not alert:
        entry["backfill"] = True
    elif prev.get("backfill"):
        entry["backfill"] = True
    suppress = (not alert) or (status == "seen" and bool(prev.get("backfill")))
    if suppress:
        if status not in entry["transitions_emitted"]:
            entry["transitions_emitted"].append(status)
    else:
        why = reason or {
            "pending": "report-written",
            "seen": "report-read",
            "answered": "reply-written",
            "delayed": "unread-or-unanswered",
        }[status]
        _record_event(state, entry, status, reason=why, read_by=read_by)
    msgs[mid] = entry
    save_delivery_state(state)
    return entry


def mark_pending_on_append(channel: str, mid: str, status: str, in_reply_to: str | None, frm: str, to: str, body: str, created: str) -> None:
    meta = {
        "from": frm,
        "to": to,
        "created_at": created,
        "in_reply_to": in_reply_to or "null",
        "message_status": status,
        "needs_reply": message_needs_reply({"status": status, "body": body, "id": mid}),
        "channel": channel,
    }
    mark_delivery(channel, mid, "pending", meta=meta, reason="report-written")
    if _blank_parent(in_reply_to) or status == "blocked":
        return
    parent = load_delivery_state()["messages"].get(in_reply_to) or {}
    if not parent:
        return
    if _from_recipient(parent, {"from": frm, "status": status}):
        mark_delivery(parent.get("channel") or channel, in_reply_to, "answered", force=True, reason="reply-written")


def append_message(channel: str, frm: str, to: str, body: str, project: str = "workspace", status: str = "open", in_reply_to: str | None = None, *, force: bool = False) -> str:
    path, expected, target = CHANNELS[channel]
    lines = body.strip().splitlines()
    if not lines or len(lines) > 12:
        raise ValueError("body must contain 1..12 lines")
    if status not in VALID_STATUS:
        raise ValueError(f"invalid status: {status}")
    allowed = _allowed(expected)
    if allowed is not None and frm not in allowed:
        raise ValueError(f"{channel} requires from in {sorted(allowed)}")
    if to != target:
        raise ValueError(f"{channel} requires to={target}")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    blocks = _parse_blocks(text)
    if status == "open" and not force:
        for block in blocks:
            if block.get("status") == "open" and block.get("from") == frm and block.get("to") == to and block.get("body", "").strip() == body.strip():
                return block["id"]
    mid = make_id(frm)
    created = now_tr().isoformat(timespec="seconds")
    record = [
        "",
        "---",
        f"id: {mid}",
        f"from: {frm}",
        f"to: {to}",
        f"in_reply_to: {in_reply_to or 'null'}",
        f"created_at: {created}",
        f"project: {project}",
        f"status: {status}",
        "---",
        "",
        body.strip(),
        "",
    ]
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(record))
    mark_pending_on_append(channel, mid, status, in_reply_to, frm, to, body, created)
    return mid


def latest_message(channel: str) -> str:
    path, _, _ = CHANNELS[channel]
    if not path.exists():
        return f"(no file: {path.name})"
    blocks = _parse_blocks(path.read_text(encoding="utf-8"))
    if not blocks:
        return f"(no messages in {channel})"
    block = blocks[-1]
    return "\n".join([f"{k}: {block.get(k, '')}" for k in ("id", "from", "to", "in_reply_to", "created_at", "project", "status")] + ["", block.get("body", "")])


def open_message_ids(channel: str) -> list[str]:
    path, _, _ = CHANNELS[channel]
    return [b["id"] for b in _parse_blocks(path.read_text(encoding="utf-8")) if b.get("status") == "open"] if path.exists() else []


def channel_status(channel: str) -> dict:
    path, _, _ = CHANNELS[channel]
    blocks = _parse_blocks(path.read_text(encoding="utf-8")) if path.exists() else []
    counts = {s: sum(b.get("status") == s for b in blocks) for s in VALID_STATUS}
    last = blocks[-1] if blocks else {}
    return {"channel": channel, "total": len(blocks), **counts, "latest_id": last.get("id"), "latest_created_at": last.get("created_at"), "path": _rel(path)}


def stale_open_ids(channel: str, older_than_hours: float = STALE_HOURS) -> list[str]:
    path, _, _ = CHANNELS[channel]
    cutoff = now_tr() - dt.timedelta(hours=older_than_hours)
    out = []
    if not path.exists():
        return out
    for block in _parse_blocks(path.read_text(encoding="utf-8")):
        if block.get("status") == "open" and block.get("id") and (parsed := _parse_created_at(block.get("created_at", ""))) and parsed < cutoff:
            out.append(block["id"])
    return out


def open_backlog_rows(channel: str | None = None) -> list[dict]:
    names = [channel] if channel else sorted(CHANNELS)
    out = []
    now = now_tr()
    for name in names:
        if name not in CHANNELS:
            continue
        path, _, _ = CHANNELS[name]
        if not path.exists():
            continue
        for block in _parse_blocks(path.read_text(encoding="utf-8")):
            if block.get("status") != "open" or "id" not in block:
                continue
            created = _parse_created_at(block.get("created_at", ""))
            age = None if created is None else round((now - created).total_seconds() / 3600, 2)
            out.append({"channel": name, "id": block["id"], "created_at": block.get("created_at", ""), "age_hours": age})
    return sorted(out, key=lambda row: (row["created_at"], row["channel"], row["id"]))


def format_backlog(channel: str | None = None) -> str:
    rows = open_backlog_rows(channel)
    ages = [row["age_hours"] for row in rows if row["age_hours"] is not None]
    return "\n".join([f"{row['channel']}\t{row['id']}\t{row['created_at']}\t{row['age_hours']}" for row in rows] + [f"total_open={len(rows)}\toldest_open_age_hours={max(ages) if ages else None}"])


def refresh_delayed(older_than_minutes: float = DELAYED_AFTER_MINUTES) -> list[str]:
    state = load_delivery_state()
    cutoff = now_tr() - dt.timedelta(minutes=older_than_minutes)
    out = []
    for mid, entry in list(state["messages"].items()):
        status = entry.get("status")
        if status == "delayed":
            out.append(mid)
            continue
        if status not in {"pending", "seen"}:
            continue
        when = _parse_created_at(entry.get("pending_at") or entry.get("updated_at") or "")
        if not when or when >= cutoff:
            continue
        if status == "seen" and not entry.get("needs_reply", True):
            continue
        if "delayed" in (entry.get("transitions_emitted") or []):
            continue
        mark_delivery(entry.get("channel", ""), mid, "delayed", reason="unread-or-unanswered")
        out.append(mid)
    return out


def delivery_summary() -> dict:
    refresh_delayed()
    state = load_delivery_state()
    counts = {s: 0 for s in DELIVERY_STATUSES}
    by = {s: [] for s in DELIVERY_STATUSES}
    for mid, entry in state["messages"].items():
        if entry.get("status") in counts:
            counts[entry["status"]] += 1
            by[entry["status"]].append(mid)
    return {
        "counts": counts,
        "by_status": by,
        "total": sum(counts.values()),
        "path": _rel(DELIVERY_PATH),
        "events": len(state.get("events") or []),
        "transport": "poll-ledger",
        "push": False,
    }


def format_delivery() -> str:
    summary = delivery_summary()
    lines = [
        f"delivery_total={summary['total']}",
        "transport=poll-ledger",
        "push=false",
        f"events={summary['events']}",
    ]
    for status in DELIVERY_STATUSES:
        lines.append(f"{status}={len(summary['by_status'][status])}")
        lines.extend(f"  {mid}" for mid in summary["by_status"][status][:30])
    return "\n".join(lines)


def load_inbox_read_state() -> dict:
    try:
        value = json.loads(INBOX_READ_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_inbox_read_state(state: dict) -> dict:
    _atomic_write(INBOX_READ_PATH, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return state


def channel_last_write_meta(channel: str) -> dict:
    blocks = _blocks_for(channel)
    last = blocks[-1] if blocks else {}
    path = _watch_map().get(channel, Path(channel))
    return {"channel": channel, "last_write_at": last.get("created_at"), "last_write_id": last.get("id"), "path": _rel(path)}


def unread_message_rows(channel: str | None = None) -> list[dict]:
    names = [channel] if channel else list(INBOX_WATCH_CHANNELS)
    state = load_inbox_read_state()
    now = now_tr()
    out = []
    watch = _watch_map()
    for name in names:
        if name not in watch and name not in CHANNELS:
            continue
        if name not in watch:
            continue
        path = watch[name]
        if not path.exists():
            continue
        last = _parse_created_at(str((state.get(name) or {}).get("last_read_at") or ""))
        for block in _blocks_for(name):
            created = _parse_created_at(block.get("created_at", ""))
            if not created or (last and created <= last) or "id" not in block:
                continue
            out.append({"channel": name, "id": block["id"], "created_at": block.get("created_at", ""), "age_hours": round((now - created).total_seconds() / 3600, 2)})
    return sorted(out, key=lambda row: (row["created_at"], row["channel"], row["id"]))


def mark_seen_for_unread(channel: str | None = None, reader: str | None = None) -> list[str]:
    ids = []
    for row in unread_message_rows(channel):
        current = (load_delivery_state()["messages"].get(row["id"]) or {}).get("status")
        if current == "answered":
            continue
        mark_delivery(row["channel"], row["id"], "seen", reason="report-read", read_by=reader)
        ids.append(row["id"])
    return ids


def mark_inbox_read(channel: str | None = None, reader: str | None = None) -> dict:
    mark_seen_for_unread(channel, reader=reader)
    state = load_inbox_read_state()
    stamp = now_tr().isoformat(timespec="seconds")
    names = [channel] if channel else list(INBOX_WATCH_CHANNELS)
    watch = _watch_map()
    for name in names:
        if name not in watch:
            continue
        meta = channel_last_write_meta(name)
        state[name] = {
            "last_read_at": meta.get("last_write_at") or stamp,
            "last_read_id": meta.get("last_write_id"),
            "read_by": reader,
        }
    return save_inbox_read_state(state)


def format_inbox(channel: str | None = None) -> str:
    rows = unread_message_rows(channel)
    lines = [f"{row['channel']}\t{row['id']}\t{row['created_at']}\t{row['age_hours']}" for row in rows] + [f"unread_total={len(rows)}"]
    state = load_inbox_read_state()
    now = now_tr()
    names = [channel] if channel else list(INBOX_WATCH_CHANNELS)
    watch = _watch_map()
    for name in names:
        if name not in watch:
            continue
        if name in INBOX_WATCH_CHANNELS and name not in CHANNELS and name != "team-reports":
            continue
        unread = unread_message_rows(name)
        ages = [(now - parsed).total_seconds() / 60 for row in unread if (parsed := _parse_created_at(row["created_at"]))]
        meta = channel_last_write_meta(name)
        lines.append(f"{name}\tlast_write={meta.get('last_write_at')}\tlast_read={(state.get(name) or {}).get('last_read_at')}\tunread_age_min={round(max(ages), 1) if ages else None}")
    return "\n".join(lines)


def channel_health(channel: str | None = None) -> dict:
    names = [channel] if channel else sorted(CHANNELS)
    problems = []
    result = {}
    inbox = load_inbox_read_state()
    now = now_tr()
    for name in names:
        if name not in CHANNELS:
            problems.append(f"unknown_channel:{name}")
            continue
        path, _, _ = CHANNELS[name]
        status = channel_status(name)
        stale = stale_open_ids(name)
        entry = {**status, "stale_open_ids": stale, "stale_open_count": len(stale)}
        if name in INBOX_WATCH_CHANNELS:
            unread = unread_message_rows(name)
            ages = [(now - parsed).total_seconds() / 60 for row in unread if (parsed := _parse_created_at(row["created_at"]))]
            age = round(max(ages), 1) if ages else None
            entry["inbox_watch"] = {
                "last_write_at": channel_last_write_meta(name).get("last_write_at"),
                "last_write_id": channel_last_write_meta(name).get("last_write_id"),
                "last_read_at": (inbox.get(name) or {}).get("last_read_at"),
                "last_read_id": (inbox.get(name) or {}).get("last_read_id"),
                "unread_count": len(unread),
                "unread_age_minutes": age,
            }
            if age is not None and age >= INBOX_UNREAD_ALARM_MINUTES:
                problems.append(f"inbox_unread:{name}:{int(age)}")
        result[name] = entry
        if not path.exists():
            problems.append(f"missing_file:{name}")
        if status["open"] >= 20:
            problems.append(f"open_count_high:{name}:{status['open']}")
        if stale:
            problems.append(f"stale_opens:{name}:{len(stale)}")
    delivery = delivery_summary()
    if delivery["counts"]["delayed"]:
        problems.append(f"delivery_delayed:{delivery['counts']['delayed']}")
    rows = open_backlog_rows(channel)
    ages = [row["age_hours"] for row in rows if row["age_hours"] is not None]
    return {
        "healthy": not problems,
        "problems": problems,
        "channels": result,
        "stale_hours": STALE_HOURS,
        "total_open": sum(item["open"] for item in result.values()),
        "oldest_open_age_hours": max(ages) if ages else None,
        "delivery": delivery,
        "transport": "poll-ledger",
        "push": False,
    }


def _from_recipient(parent: dict, child: dict) -> bool:
    """A reply closes the parent only when the parent's recipient writes it."""
    if (child.get("status") or "").lower() == "blocked":
        return False
    author = (child.get("from") or "").lower()
    parent_from = (parent.get("from") or "").lower()
    expected = (parent.get("to") or "").lower()
    if not author or author == parent_from:
        return False
    if expected == "team":
        return True
    if expected == "grok":
        return author in {"grok", "grok-bot", "grok-api"}
    return author == expected


def _reply_index(blocks: list[dict]) -> set[str]:
    by_id = {block["id"]: block for block in blocks if block.get("id")}
    parents = set()
    for block in blocks:
        parent_id = block.get("in_reply_to") or ""
        if _blank_parent(parent_id):
            continue
        parent = by_id.get(parent_id)
        if parent is None:
            continue
        if _from_recipient(parent, block):
            parents.add(parent_id)
    return parents


def _load_health() -> dict:
    try:
        value = json.loads(HEALTH_PATH.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _health_body(ok: bool, error: str | None, summary: dict | None) -> dict:
    previous = _load_health()
    state = load_delivery_state()
    counts = {status: 0 for status in DELIVERY_STATUSES}
    for entry in state["messages"].values():
        if entry.get("status") in counts:
            counts[entry["status"]] += 1
    failures = 0 if ok else int(previous.get("consecutive_failures") or 0) + 1
    return {
        "ok": ok,
        "consecutive_failures": failures,
        "last_error": error,
        "retry": "workflow job fails closed; next schedule (*/15) or workflow_dispatch reruns reconcile. Unsaved transitions stay absent and are retried. Emitted event keys are not repeated.",
        "transport": "poll-ledger",
        "push": False,
        "push_tested_to_chat": False,
        "push_limit": PUSH_LIMIT,
        "schedule": "*/15 * * * *",
        "schedule_is_best_effort": True,
        "delay_threshold_minutes": DELAYED_AFTER_MINUTES,
        "counts": counts,
        "event_count": len(state.get("events") or []),
        "event_keys": list(state.get("event_keys") or []),
        "new_event_keys": (summary or {}).get("new_event_keys") or [],
        "delivery_path": _rel(DELIVERY_PATH),
        "read_path": _rel(INBOX_READ_PATH),
    }


def _write_health(ok: bool, error: str | None, summary: dict | None) -> bool:
    body = _health_body(ok, error, summary)
    previous = _load_health()
    comparable = ("ok", "consecutive_failures", "last_error", "counts", "event_count", "event_keys", "push")
    if previous and all(previous.get(key) == body.get(key) for key in comparable):
        return False
    body["checked_at"] = now_tr().isoformat(timespec="seconds")
    _atomic_write(HEALTH_PATH, json.dumps(body, ensure_ascii=False, indent=2) + "\n")
    return True


def _meta_from_block(channel: str, block: dict) -> dict:
    return {
        "from": block.get("from") or "",
        "to": block.get("to") or ("team" if channel in {"shared-inbox", "team-reports"} else ""),
        "created_at": block.get("created_at") or "",
        "in_reply_to": block.get("in_reply_to") or "null",
        "message_status": block.get("status") or "",
        "needs_reply": message_needs_reply({**block, "_channel": channel}),
        "channel": channel,
    }


def _desired_status(channel: str, block: dict, replies: set[str], existing: dict, fresh: bool) -> str:
    msg_status = (block.get("status") or "").lower()
    mid = block["id"]
    if mid in replies or msg_status == "superseded":
        return "answered"
    if existing.get("status") == "answered":
        return "answered"
    if existing.get("status") == "seen":
        return "seen"
    if existing.get("status") == "delayed":
        return "delayed"
    if not existing and not fresh and channel != "team-reports" and msg_status in {"done", "blocked"}:
        return "answered"
    if not existing and not fresh and msg_status in OPEN_LIKE | {"", "done"}:
        if channel == "team-reports" or msg_status in OPEN_LIKE:
            return "delayed"
        if msg_status == "done":
            return "answered"
    return "pending"


def reconcile_delivery() -> dict:
    blocks: list[tuple[str, dict]] = []
    for name in list(CHANNELS) + ["team-reports"]:
        for block in _blocks_for(name):
            blocks.append((name, block))
    replies = _reply_index([block for _, block in blocks])
    before = set(load_delivery_state().get("event_keys") or [])
    now = now_tr()
    for channel, block in blocks:
        mid = block.get("id")
        if not mid:
            continue
        existing = load_delivery_state()["messages"].get(mid) or {}
        created = _parse_created_at(block.get("created_at", ""))
        age_min = None if created is None else (now - created).total_seconds() / 60
        fresh = age_min is not None and age_min < DELAYED_AFTER_MINUTES
        desired = _desired_status(channel, block, replies, existing, fresh)
        meta = _meta_from_block(channel, block)
        if not existing:
            if desired == "delayed":
                mark_delivery(channel, mid, "pending", alert=False, meta=meta)
                mark_delivery(channel, mid, "delayed", alert=True, meta=meta, reason="unread-or-unanswered")
            elif desired == "answered":
                mark_delivery(channel, mid, "answered", alert=fresh, meta=meta, reason="reply-written")
            else:
                mark_delivery(channel, mid, "pending", alert=True, meta=meta, reason="report-written")
            continue
        if desired != existing.get("status"):
            historical = bool(existing.get("backfill")) and not fresh
            alert = not (historical and desired in {"answered", "seen"})
            mark_delivery(channel, mid, desired, alert=alert, meta=meta)
    refresh_delayed()
    after = load_delivery_state()
    new_keys = [key for key in after.get("event_keys") or [] if key not in before]
    summary = delivery_summary()
    summary["new_event_keys"] = new_keys
    summary["push"] = False
    summary["transport"] = "poll-ledger"
    return summary


def reconcile_main() -> int:
    try:
        summary = reconcile_delivery()
    except Exception as exc:
        _write_health(False, f"{type(exc).__name__}: {exc}"[:400], None)
        print(json.dumps({"ok": False, "error": type(exc).__name__, "push": False}, ensure_ascii=False))
        return 1
    _write_health(True, None, summary)
    print(json.dumps({"ok": True, "push": False, "transport": "poll-ledger", "new_event_keys": summary.get("new_event_keys"), "counts": summary.get("counts"), "events": summary.get("events")}, ensure_ascii=False))
    return 0


def list_channels() -> str:
    return "\n".join(f"{name}\tfrom={'any' if expected is None else ','.join(sorted(_allowed(expected)))}\tto={target}\t{_rel(path)}" for name, (path, expected, target) in sorted(CHANNELS.items()))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="send")
    parser.add_argument("channel", nargs="?", choices=sorted(set(CHANNELS) | {"team-reports"}))
    parser.add_argument("--from", dest="frm")
    parser.add_argument("--to")
    parser.add_argument("--body")
    parser.add_argument("--project", default="workspace")
    parser.add_argument("--status", default="open", choices=sorted(VALID_STATUS))
    parser.add_argument("--in-reply-to")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--mark", action="store_true")
    parser.add_argument("--reader")
    args = parser.parse_args()
    cmd = args.command
    channel = args.channel
    if cmd in CHANNELS and channel is None:
        channel, cmd = cmd, "send"
    if cmd == "list-channels":
        print(list_channels())
        return
    if cmd == "backlog":
        print(format_backlog(channel if channel in CHANNELS else None))
        return
    if cmd in {"inbox", "unread"}:
        print(format_inbox(channel))
        if args.mark:
            mark_inbox_read(channel, reader=args.reader)
        return
    if cmd == "mark-read":
        if not channel:
            parser.error("mark-read requires a channel")
        print(json.dumps(mark_inbox_read(channel, reader=args.reader), ensure_ascii=False))
        return
    if cmd == "reconcile":
        raise SystemExit(reconcile_main())
    if cmd in {"delivery", "notify"}:
        print(format_delivery())
        return
    if cmd == "health":
        print(json.dumps(channel_health(channel if channel in CHANNELS else None), indent=2))
        return
    if cmd == "latest":
        print(latest_message(channel))
        return
    if cmd == "open":
        print("\n".join(open_message_ids(channel)) or "(none)")
        return
    if cmd == "status":
        print(json.dumps(channel_status(channel), indent=2))
        return
    if cmd == "stale":
        print("\n".join(stale_open_ids(channel)) or "(none)")
        return
    if not args.frm or not args.to or args.body is None:
        parser.error("send requires --from, --to, and --body")
    print(append_message(channel, args.frm, args.to, args.body, args.project, args.status, args.in_reply_to, force=args.force))


if __name__ == "__main__":
    main()
