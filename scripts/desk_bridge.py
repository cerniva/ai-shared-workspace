#!/usr/bin/env python3
"""File-desk bridge with message, inbox, and delivery tracking."""
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
}
VALID_STATUS = {"open", "done", "blocked", "queued"}
STALE_HOURS = 24
INBOX_WATCH_CHANNELS = ("chatgpt-to-grok", "grok-to-chatgpt", "chatgpt-to-gemini", "gemini-to-chatgpt")
INBOX_UNREAD_ALARM_MINUTES = 10
INBOX_READ_PATH = ROOT / "state" / "inbox_read.json"
DELIVERY_PATH = ROOT / "state" / "message_delivery.json"
DELIVERY_STATUSES = ("pending", "seen", "answered", "delayed")
DELAYED_AFTER_MINUTES = 30
_SPLIT = re.compile(r"(?m)^---\s*$")


def now_tr() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))


def make_id(agent: str) -> str:
    n = now_tr()
    return f"MSG-{n.strftime('%Y%m%d-%H%M%S')}-{n.microsecond:06d}-{agent.replace('_','').replace(' ','')}-bridge"


def _parse_created_at(value: str) -> dt.datetime | None:
    try:
        x = dt.datetime.fromisoformat(value)
    except (TypeError, ValueError):
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


def _allowed(expected: str | FrozenSet[str] | None) -> set[str] | None:
    return None if expected is None else ({expected} if isinstance(expected, str) else set(expected))


def load_delivery_state() -> dict:
    try:
        value = json.loads(DELIVERY_PATH.read_text(encoding="utf-8"))
        if isinstance(value, dict) and isinstance(value.get("messages"), dict):
            return value
    except (OSError, json.JSONDecodeError):
        pass
    return {"messages": {}}


def save_delivery_state(state: dict) -> None:
    DELIVERY_PATH.parent.mkdir(parents=True, exist_ok=True)
    state.setdefault("messages", {})
    DELIVERY_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def mark_delivery(channel: str, mid: str, status: str, *, force: bool = False) -> dict:
    if status not in DELIVERY_STATUSES:
        raise ValueError(f"invalid delivery status: {status}")
    state = load_delivery_state(); msgs = state["messages"]; prev = msgs.get(mid) or {}
    if not force and status == "pending" and prev.get("status") == "pending": return prev
    if not force and prev.get("status") == "answered" and status in ("pending", "seen", "delayed"): return prev
    stamp = now_tr().isoformat(timespec="seconds")
    entry = {"id": mid, "channel": channel, "status": status, "updated_at": stamp, "alerted": status == "pending" or bool(prev.get("alerted"))}
    if "pending_at" in prev: entry["pending_at"] = prev["pending_at"]
    if status == "pending": entry["pending_at"] = prev.get("pending_at") or stamp; entry["alerted"] = True
    if "seen_at" in prev: entry["seen_at"] = prev["seen_at"]
    if status == "seen": entry["seen_at"] = prev.get("seen_at") or stamp
    if status == "answered": entry["answered_at"] = stamp
    if status == "delayed": entry["delayed_at"] = stamp
    msgs[mid] = entry; save_delivery_state(state); return entry


def mark_pending_on_append(channel: str, mid: str, status: str, in_reply_to: str | None) -> None:
    if status in ("open", "queued"): mark_delivery(channel, mid, "pending")
    if in_reply_to and in_reply_to != "null":
        parent = load_delivery_state()["messages"].get(in_reply_to) or {}
        mark_delivery(parent.get("channel") or channel, in_reply_to, "answered", force=True)
    if status == "done": mark_delivery(channel, mid, "answered", force=True)


def append_message(channel: str, frm: str, to: str, body: str, project: str = "workspace", status: str = "open", in_reply_to: str | None = None, *, force: bool = False) -> str:
    path, expected, target = CHANNELS[channel]
    lines = body.strip().splitlines()
    if not lines or len(lines) > 12: raise ValueError("body must contain 1..12 lines")
    if status not in VALID_STATUS: raise ValueError(f"invalid status: {status}")
    allowed = _allowed(expected)
    if allowed is not None and frm not in allowed: raise ValueError(f"{channel} requires from in {sorted(allowed)}")
    if to != target: raise ValueError(f"{channel} requires to={target}")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    blocks = _parse_blocks(text)
    if status == "open" and not force:
        for b in blocks:
            if b.get("status") == "open" and b.get("from") == frm and b.get("to") == to and b.get("body", "").strip() == body.strip(): return b["id"]
    mid = make_id(frm); created = now_tr().isoformat(timespec="seconds")
    block = ["", "---", f"id: {mid}", f"from: {frm}", f"to: {to}", f"in_reply_to: {in_reply_to or 'null'}", f"created_at: {created}", f"project: {project}", f"status: {status}", "---", "", body.strip(), ""]
    with path.open("a", encoding="utf-8") as f: f.write("\n".join(block))
    mark_pending_on_append(channel, mid, status, in_reply_to)
    return mid


def latest_message(channel: str) -> str:
    path, _, _ = CHANNELS[channel]
    if not path.exists(): return f"(no file: {path.name})"
    blocks = _parse_blocks(path.read_text(encoding="utf-8"))
    if not blocks: return f"(no messages in {channel})"
    b = blocks[-1]
    return "\n".join([f"{k}: {b.get(k, '')}" for k in ("id", "from", "to", "in_reply_to", "created_at", "project", "status")] + ["", b.get("body", "")])


def open_message_ids(channel: str) -> list[str]:
    path, _, _ = CHANNELS[channel]
    return [b["id"] for b in _parse_blocks(path.read_text(encoding="utf-8")) if b.get("status") == "open"] if path.exists() else []


def channel_status(channel: str) -> dict:
    path, _, _ = CHANNELS[channel]; blocks = _parse_blocks(path.read_text(encoding="utf-8")) if path.exists() else []
    counts = {s: sum(b.get("status") == s for b in blocks) for s in VALID_STATUS}; last = blocks[-1] if blocks else {}
    return {"channel": channel, "total": len(blocks), **counts, "latest_id": last.get("id"), "latest_created_at": last.get("created_at"), "path": _rel(path)}


def stale_open_ids(channel: str, older_than_hours: float = STALE_HOURS) -> list[str]:
    path, _, _ = CHANNELS[channel]; cutoff = now_tr() - dt.timedelta(hours=older_than_hours); out = []
    if not path.exists(): return out
    for b in _parse_blocks(path.read_text(encoding="utf-8")):
        if b.get("status") == "open" and b.get("id") and (x := _parse_created_at(b.get("created_at", ""))) and x < cutoff: out.append(b["id"])
    return out


def open_backlog_rows(channel: str | None = None) -> list[dict]:
    names = [channel] if channel else sorted(CHANNELS); out = []; now = now_tr()
    for name in names:
        if name not in CHANNELS: continue
        path, _, _ = CHANNELS[name]
        if not path.exists(): continue
        for b in _parse_blocks(path.read_text(encoding="utf-8")):
            if b.get("status") != "open" or "id" not in b: continue
            created = _parse_created_at(b.get("created_at", "")); age = None if created is None else round((now - created).total_seconds()/3600, 2)
            out.append({"channel": name, "id": b["id"], "created_at": b.get("created_at", ""), "age_hours": age})
    return sorted(out, key=lambda r: (r["created_at"], r["channel"], r["id"]))


def format_backlog(channel: str | None = None) -> str:
    rows = open_backlog_rows(channel); ages = [r["age_hours"] for r in rows if r["age_hours"] is not None]
    return "\n".join([f"{r['channel']}\t{r['id']}\t{r['created_at']}\t{r['age_hours']}" for r in rows] + [f"total_open={len(rows)}\toldest_open_age_hours={max(ages) if ages else None}"])


def refresh_delayed(older_than_minutes: float = DELAYED_AFTER_MINUTES) -> list[str]:
    state = load_delivery_state(); cutoff = now_tr() - dt.timedelta(minutes=older_than_minutes); out = []
    for mid, entry in list(state["messages"].items()):
        if entry.get("status") not in ("pending", "seen", "delayed"): continue
        when = _parse_created_at(entry.get("pending_at") or entry.get("updated_at") or "")
        if when and when < cutoff:
            if entry.get("status") != "delayed": mark_delivery(entry.get("channel", ""), mid, "delayed")
            out.append(mid)
    return out


def delivery_summary() -> dict:
    refresh_delayed(); state = load_delivery_state(); counts = {s: 0 for s in DELIVERY_STATUSES}; by = {s: [] for s in DELIVERY_STATUSES}
    for mid, entry in state["messages"].items():
        if entry.get("status") in counts: counts[entry["status"]] += 1; by[entry["status"]].append(mid)
    return {"counts": counts, "by_status": by, "total": sum(counts.values()), "path": _rel(DELIVERY_PATH)}


def format_delivery() -> str:
    x = delivery_summary(); lines = [f"delivery_total={x['total']}"]
    for status in DELIVERY_STATUSES: lines.append(f"{status}={len(x['by_status'][status])}"); lines.extend(f"  {mid}" for mid in x["by_status"][status][:30])
    return "\n".join(lines)


def load_inbox_read_state() -> dict:
    try:
        x = json.loads(INBOX_READ_PATH.read_text(encoding="utf-8")); return x if isinstance(x, dict) else {}
    except (OSError, json.JSONDecodeError): return {}


def save_inbox_read_state(state: dict) -> dict:
    INBOX_READ_PATH.parent.mkdir(parents=True, exist_ok=True); INBOX_READ_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def channel_last_write_meta(channel: str) -> dict:
    path, _, _ = CHANNELS[channel]; blocks = _parse_blocks(path.read_text(encoding="utf-8")) if path.exists() else []; last = blocks[-1] if blocks else {}
    return {"channel": channel, "last_write_at": last.get("created_at"), "last_write_id": last.get("id"), "path": _rel(path)}


def unread_message_rows(channel: str | None = None) -> list[dict]:
    names = [channel] if channel else list(INBOX_WATCH_CHANNELS); state = load_inbox_read_state(); now = now_tr(); out = []
    for name in names:
        if name not in CHANNELS: continue
        path, _, _ = CHANNELS[name]
        if not path.exists(): continue
        last = _parse_created_at(str((state.get(name) or {}).get("last_read_at") or ""))
        for b in _parse_blocks(path.read_text(encoding="utf-8")):
            created = _parse_created_at(b.get("created_at", ""))
            if not created or (last and created <= last) or "id" not in b: continue
            out.append({"channel": name, "id": b["id"], "created_at": b.get("created_at", ""), "age_hours": round((now-created).total_seconds()/3600, 2)})
    return sorted(out, key=lambda r: (r["created_at"], r["channel"], r["id"]))


def mark_seen_for_unread(channel: str | None = None) -> list[str]:
    ids = []
    for row in unread_message_rows(channel):
        if (load_delivery_state()["messages"].get(row["id"]) or {}).get("status") != "answered": mark_delivery(row["channel"], row["id"], "seen"); ids.append(row["id"])
    return ids


def mark_inbox_read(channel: str | None = None) -> dict:
    mark_seen_for_unread(channel); state = load_inbox_read_state(); stamp = now_tr().isoformat(timespec="seconds"); names = [channel] if channel else list(INBOX_WATCH_CHANNELS)
    for name in names:
        if name in CHANNELS:
            meta = channel_last_write_meta(name); state[name] = {"last_read_at": meta.get("last_write_at") or stamp, "last_read_id": meta.get("last_write_id")}
    save_inbox_read_state(state); return state


def format_inbox(channel: str | None = None) -> str:
    rows = unread_message_rows(channel); lines = [f"{r['channel']}\t{r['id']}\t{r['created_at']}\t{r['age_hours']}" for r in rows] + [f"unread_total={len(rows)}"]; state = load_inbox_read_state(); now = now_tr(); names = [channel] if channel else list(INBOX_WATCH_CHANNELS)
    for name in names:
        if name not in CHANNELS: continue
        unread = unread_message_rows(name); ages = [(now-_parse_created_at(r["created_at"])).total_seconds()/60 for r in unread if _parse_created_at(r["created_at"])]
        meta = channel_last_write_meta(name); lines.append(f"{name}\tlast_write={meta.get('last_write_at')}\tlast_read={(state.get(name) or {}).get('last_read_at')}\tunread_age_min={round(max(ages),1) if ages else None}")
    return "\n".join(lines)


def channel_health(channel: str | None = None) -> dict:
    names = [channel] if channel else sorted(CHANNELS); problems = []; result = {}; inbox = load_inbox_read_state(); now = now_tr()
    for name in names:
        if name not in CHANNELS: problems.append(f"unknown_channel:{name}"); continue
        path, _, _ = CHANNELS[name]; st = channel_status(name); stale = stale_open_ids(name); entry = {**st, "stale_open_ids": stale, "stale_open_count": len(stale)}
        if name in INBOX_WATCH_CHANNELS:
            unread = unread_message_rows(name); ages = [(now-_parse_created_at(r["created_at"])).total_seconds()/60 for r in unread if _parse_created_at(r["created_at"])]; age = round(max(ages),1) if ages else None
            entry["inbox_watch"] = {"last_write_at": channel_last_write_meta(name).get("last_write_at"), "last_write_id": channel_last_write_meta(name).get("last_write_id"), "last_read_at": (inbox.get(name) or {}).get("last_read_at"), "last_read_id": (inbox.get(name) or {}).get("last_read_id"), "unread_count": len(unread), "unread_age_minutes": age}
            if age is not None and age >= INBOX_UNREAD_ALARM_MINUTES: problems.append(f"inbox_unread:{name}:{int(age)}")
        result[name] = entry
        if not path.exists(): problems.append(f"missing_file:{name}")
        if st["open"] >= 20: problems.append(f"open_count_high:{name}:{st['open']}")
        if stale: problems.append(f"stale_opens:{name}:{len(stale)}")
    delivery = delivery_summary()
    if delivery["counts"]["delayed"]: problems.append(f"delivery_delayed:{delivery['counts']['delayed']}")
    rows = open_backlog_rows(channel); ages = [r["age_hours"] for r in rows if r["age_hours"] is not None]
    return {"healthy": not problems, "problems": problems, "channels": result, "stale_hours": STALE_HOURS, "total_open": sum(x["open"] for x in result.values()), "oldest_open_age_hours": max(ages) if ages else None, "delivery": delivery}


def list_channels() -> str:
    return "\n".join(f"{n}\tfrom={'any' if e is None else ','.join(sorted(_allowed(e)))}\tto={t}\t{_rel(p)}" for n,(p,e,t) in sorted(CHANNELS.items()))


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("command", nargs="?", default="send"); p.add_argument("channel", nargs="?", choices=sorted(CHANNELS)); p.add_argument("--from", dest="frm"); p.add_argument("--to"); p.add_argument("--body"); p.add_argument("--project", default="workspace"); p.add_argument("--status", default="open", choices=sorted(VALID_STATUS)); p.add_argument("--in-reply-to"); p.add_argument("--force", action="store_true"); p.add_argument("--mark", action="store_true"); a = p.parse_args(); cmd = a.command; channel = a.channel
    if cmd in CHANNELS and channel is None: channel, cmd = cmd, "send"
    if cmd == "list-channels": print(list_channels()); return
    if cmd == "backlog": print(format_backlog(channel)); return
    if cmd in ("inbox", "unread"): print(format_inbox(channel)); (mark_inbox_read(channel) if a.mark else None); return
    if cmd in ("delivery", "notify"): print(format_delivery()); return
    if cmd == "health": print(json.dumps(channel_health(channel), indent=2)); return
    if cmd == "latest": print(latest_message(channel)); return
    if cmd == "open": print("\n".join(open_message_ids(channel)) or "(none)"); return
    if cmd == "status": print(json.dumps(channel_status(channel), indent=2)); return
    if cmd == "stale": print("\n".join(stale_open_ids(channel)) or "(none)"); return
    if not a.frm or not a.to or a.body is None: p.error("send requires --from, --to, and --body")
    print(append_message(channel, a.frm, a.to, a.body, a.project, a.status, a.in_reply_to, force=a.force))


if __name__ == "__main__": main()
