#!/usr/bin/env python3
"""File-desk bridge: append protocol-safe agent handoffs without rewriting history."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import FrozenSet

ROOT = Path(__file__).resolve().parents[1]
# expected_from: None (any), str, or frozenset/set of allowed aliases
CHANNELS: dict[str, tuple[Path, str | FrozenSet[str] | set[str] | None, str]] = {
    "grok-to-chatgpt": (
        ROOT / "messages" / "grok-to-chatgpt.md",
        frozenset({"grok", "grok-bot"}),
        "chatgpt",
    ),
    "chatgpt-to-grok": (ROOT / "messages" / "chatgpt-to-grok.md", "chatgpt", "grok"),
    "inbox-gemini": (ROOT / "messages" / "inbox-gemini.md", None, "gemini"),
    "gemini-to-chatgpt": (
        ROOT / "messages" / "gemini-to-chatgpt.md",
        "gemini",
        "chatgpt",
    ),
    "chatgpt-to-gemini": (
        ROOT / "messages" / "chatgpt-to-gemini.md",
        "chatgpt",
        "gemini",
    ),
}
VALID_STATUS = {"open", "done", "blocked", "queued"}
STALE_HOURS = 24
_MSG_SPLIT = re.compile(r"(?m)^---\s*$")
_OPEN_HIGH = 20


def now_tr() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))


def make_id(agent: str) -> str:
    safe = agent.replace("_", "").replace(" ", "")
    n = now_tr()
    # microseconds avoid same-second collisions (e.g. force=True duplicate append)
    return f"MSG-{n.strftime('%Y%m%d-%H%M%S')}-{n.microsecond:06d}-{safe}-bridge"


def _allowed_from(expected_from: str | FrozenSet[str] | set[str] | None) -> set[str] | None:
    if expected_from is None:
        return None
    if isinstance(expected_from, str):
        return {expected_from}
    return set(expected_from)


def _parse_created_at(value: str) -> dt.datetime | None:
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone(dt.timedelta(hours=3)))
    return parsed


def _normalize_body(body: str) -> str:
    return body.strip()


def _find_open_duplicate(
    blocks: list[dict[str, str]], frm: str, to: str, body: str
) -> str | None:
    norm = _normalize_body(body)
    for b in blocks:
        if b.get("status") != "open":
            continue
        if b.get("from") != frm or b.get("to") != to:
            continue
        if _normalize_body(b.get("body", "")) == norm:
            return b.get("id")
    return None


def append_message(
    channel: str,
    frm: str,
    to: str,
    body: str,
    project: str = "workspace",
    status: str = "open",
    in_reply_to: str | None = None,
    *,
    force: bool = False,
) -> str:
    path, expected_from, expected_to = CHANNELS[channel]
    lines = body.strip().splitlines()
    if not lines or len(lines) > 12:
        raise ValueError("body must contain 1..12 lines")
    if status not in VALID_STATUS:
        raise ValueError(f"invalid status: {status}")
    allowed = _allowed_from(expected_from)
    if allowed is not None and frm not in allowed:
        raise ValueError(f"{channel} requires from in {sorted(allowed)}")
    if to != expected_to:
        raise ValueError(f"{channel} requires to={expected_to}")

    path.parent.mkdir(parents=True, exist_ok=True)
    existing_text = path.read_text(encoding="utf-8") if path.exists() else ""
    blocks = _parse_blocks(existing_text) if existing_text else []

    if status == "open" and not force:
        dup_id = _find_open_duplicate(blocks, frm, to, body)
        if dup_id:
            return dup_id

    mid = make_id(frm)
    created = now_tr().isoformat(timespec="seconds")
    block = [
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
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(block))
    return mid


def _parse_blocks(text: str) -> list[dict[str, str]]:
    """Parse message file into blocks with header fields + body."""
    parts = _MSG_SPLIT.split(text)
    blocks: list[dict[str, str]] = []
    # After split on ---, pattern is: [preamble, headers, body, headers, body, ...]
    i = 1
    while i + 1 < len(parts):
        header_raw = parts[i].strip()
        body_raw = parts[i + 1]
        # Next segment after body may start next header; body is until next --- already split
        fields: dict[str, str] = {}
        for line in header_raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                fields[k.strip()] = v.strip()
        if "id" in fields:
            fields["body"] = body_raw.strip()
            blocks.append(fields)
        i += 2
    return blocks


def latest_message(channel: str) -> str:
    path, _, _ = CHANNELS[channel]
    if not path.exists():
        return f"(no file: {path.name})"
    blocks = _parse_blocks(path.read_text(encoding="utf-8"))
    if not blocks:
        return f"(no messages in {channel})"
    b = blocks[-1]
    lines = [
        f"id: {b.get('id', '')}",
        f"from: {b.get('from', '')}",
        f"to: {b.get('to', '')}",
        f"in_reply_to: {b.get('in_reply_to', 'null')}",
        f"created_at: {b.get('created_at', '')}",
        f"project: {b.get('project', '')}",
        f"status: {b.get('status', '')}",
        "",
        b.get("body", ""),
    ]
    return "\n".join(lines)


def open_message_ids(channel: str) -> list[str]:
    path, _, _ = CHANNELS[channel]
    if not path.exists():
        return []
    blocks = _parse_blocks(path.read_text(encoding="utf-8"))
    return [b["id"] for b in blocks if b.get("status") == "open" and "id" in b]


def channel_status(channel: str) -> dict:
    """Counts + latest metadata for one channel."""
    path, _, _ = CHANNELS[channel]
    try:
        rel = str(path.relative_to(ROOT))
    except ValueError:
        rel = str(path)
    counts = {"open": 0, "done": 0, "blocked": 0, "queued": 0}
    latest_id = None
    latest_created_at = None
    total = 0
    if path.exists():
        blocks = _parse_blocks(path.read_text(encoding="utf-8"))
        total = len(blocks)
        for b in blocks:
            st = b.get("status", "")
            if st in counts:
                counts[st] += 1
        if blocks:
            last = blocks[-1]
            latest_id = last.get("id")
            latest_created_at = last.get("created_at")
    return {
        "channel": channel,
        "total": total,
        "open": counts["open"],
        "done": counts["done"],
        "blocked": counts["blocked"],
        "queued": counts["queued"],
        "latest_id": latest_id,
        "latest_created_at": latest_created_at,
        "path": rel,
    }


def stale_open_ids(channel: str, older_than_hours: float = STALE_HOURS) -> list[str]:
    """Return open message ids whose created_at is older than now-TR - hours."""
    path, _, _ = CHANNELS[channel]
    if not path.exists():
        return []
    cutoff = now_tr() - dt.timedelta(hours=older_than_hours)
    blocks = _parse_blocks(path.read_text(encoding="utf-8"))
    stale: list[str] = []
    for b in blocks:
        if b.get("status") != "open" or "id" not in b:
            continue
        created = _parse_created_at(b.get("created_at", ""))
        if created is None:
            continue
        if created < cutoff:
            stale.append(b["id"])
    return stale



def open_backlog_rows(channel: str | None = None) -> list[dict]:
    """Open messages across channels: channel, id, created_at, age_hours."""
    names = [channel] if channel else sorted(CHANNELS)
    now = now_tr()
    rows: list[dict] = []
    for name in names:
        if name not in CHANNELS:
            continue
        path, _, _ = CHANNELS[name]
        if not path.exists():
            continue
        blocks = _parse_blocks(path.read_text(encoding="utf-8"))
        for b in blocks:
            if b.get("status") != "open" or "id" not in b:
                continue
            created_s = b.get("created_at", "")
            created = _parse_created_at(created_s)
            if created is None:
                age = None
            else:
                age = round((now - created).total_seconds() / 3600.0, 2)
            rows.append(
                {
                    "channel": name,
                    "id": b["id"],
                    "created_at": created_s,
                    "age_hours": age,
                }
            )
    rows.sort(key=lambda r: (r["created_at"] or "", r["channel"], r["id"]))
    return rows


def format_backlog(channel: str | None = None) -> str:
    rows = open_backlog_rows(channel)
    lines = [
        f"{r['channel']}\t{r['id']}\t{r['created_at']}\t{r['age_hours']}"
        for r in rows
    ]
    ages = [r["age_hours"] for r in rows if r["age_hours"] is not None]
    oldest = max(ages) if ages else None
    lines.append(f"total_open={len(rows)}\toldest_open_age_hours={oldest}")
    return "\n".join(lines)


def channel_health(channel: str | None = None) -> dict:
    """Per-channel status plus problems (missing file, open_count high, stale opens)."""
    names = [channel] if channel else sorted(CHANNELS)
    channels_out: dict[str, dict] = {}
    problems: list[str] = []
    for name in names:
        if name not in CHANNELS:
            problems.append(f"unknown_channel:{name}")
            continue
        path, _, _ = CHANNELS[name]
        st = channel_status(name)
        stale = stale_open_ids(name, STALE_HOURS) if path.exists() else []
        entry = {**st, "stale_open_ids": stale, "stale_open_count": len(stale)}
        channels_out[name] = entry
        if not path.exists():
            problems.append(f"missing_file:{name}")
        if st["open"] >= _OPEN_HIGH:
            problems.append(f"open_count_high:{name}:{st['open']}")
        if stale:
            problems.append(f"stale_opens:{name}:{len(stale)}")
    total_open = sum(ch.get("open", 0) for ch in channels_out.values())
    ages = [
        r["age_hours"]
        for r in open_backlog_rows(channel)
        if r.get("age_hours") is not None
    ]
    oldest_age = max(ages) if ages else None
    return {
        "healthy": not problems,
        "problems": problems,
        "channels": channels_out,
        "stale_hours": STALE_HOURS,
        "total_open": total_open,
        "oldest_open_age_hours": oldest_age,
    }


def list_channels() -> str:
    rows = []
    for name in sorted(CHANNELS):
        path, ef, et = CHANNELS[name]
        allowed = _allowed_from(ef)
        from_s = "any" if allowed is None else ",".join(sorted(allowed))
        try:
            rel = str(path.relative_to(ROOT))
        except ValueError:
            rel = str(path)
        rows.append(f"{name}\tfrom={from_s}\tto={et}\t{rel}")
    return "\n".join(rows)


def main() -> None:
    p = argparse.ArgumentParser(description="Append/query protocol-safe desk messages")
    p.add_argument(
        "command",
        nargs="?",
        default="send",
        help="send (default) | latest | open | list-channels | status | health | stale | backlog",
    )
    p.add_argument(
        "channel",
        nargs="?",
        choices=sorted(CHANNELS),
        help="channel name (required for send/latest/open/status/stale; optional for health/backlog)",
    )
    p.add_argument("--from", dest="frm")
    p.add_argument("--to")
    p.add_argument("--body")
    p.add_argument("--project", default="workspace")
    p.add_argument("--status", default="open", choices=sorted(VALID_STATUS))
    p.add_argument("--in-reply-to")
    p.add_argument(
        "--force",
        action="store_true",
        help="append even if an identical open duplicate exists",
    )
    p.add_argument(
        "--hours",
        type=float,
        default=STALE_HOURS,
        help=f"stale threshold in hours (default {STALE_HOURS})",
    )
    p.add_argument(
        "--list-channels",
        action="store_true",
        help="print channels and exit",
    )
    a = p.parse_args()

    if a.list_channels or a.command == "list-channels":
        print(list_channels())
        return

    # Back-compat: first positional may be channel when command omitted
    # argparse: if user runs `desk_bridge.py grok-to-chatgpt --from ...`
    # then command=grok-to-chatgpt and channel=None
    cmd = a.command
    channel = a.channel
    if cmd in CHANNELS and channel is None:
        channel = cmd
        cmd = "send"
    if cmd == "backlog":
        print(format_backlog(channel))
        return
    if cmd == "health":
        print(json.dumps(channel_health(channel), ensure_ascii=False, indent=2))
        return
    if cmd == "send" and channel is None:
        p.error("channel required for send")
    if cmd in ("latest", "open", "send", "status", "stale") and channel is None:
        p.error(f"channel required for {cmd}")

    if cmd == "latest":
        print(latest_message(channel))
        return
    if cmd == "open":
        ids = open_message_ids(channel)
        if ids:
            print("\n".join(ids))
        else:
            print("(none)")
        return
    if cmd == "status":
        st = channel_status(channel)
        print(json.dumps(st, ensure_ascii=False, indent=2))
        return
    if cmd == "stale":
        ids = stale_open_ids(channel, older_than_hours=a.hours)
        if ids:
            print("\n".join(ids))
        else:
            print("(none)")
        return
    if cmd != "send":
        p.error(f"unknown command: {cmd}")

    if not a.frm or not a.to or a.body is None:
        p.error("send requires --from, --to, and --body")
    print(
        append_message(
            channel,
            a.frm,
            a.to,
            a.body,
            a.project,
            a.status,
            a.in_reply_to,
            force=a.force,
        )
    )


if __name__ == "__main__":
    main()
