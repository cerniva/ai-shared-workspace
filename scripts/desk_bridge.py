#!/usr/bin/env python3
"""File-desk bridge: append protocol-safe agent handoffs without rewriting history."""
from __future__ import annotations

import argparse
import datetime as dt
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
_MSG_SPLIT = re.compile(r"(?m)^---\s*$")


def now_tr() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))


def make_id(agent: str) -> str:
    safe = agent.replace("_", "").replace(" ", "")
    return f"MSG-{now_tr().strftime('%Y%m%d-%H%M%S')}-{safe}-bridge"


def _allowed_from(expected_from: str | FrozenSet[str] | set[str] | None) -> set[str] | None:
    if expected_from is None:
        return None
    if isinstance(expected_from, str):
        return {expected_from}
    return set(expected_from)


def append_message(
    channel: str,
    frm: str,
    to: str,
    body: str,
    project: str = "workspace",
    status: str = "open",
    in_reply_to: str | None = None,
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
    path.parent.mkdir(parents=True, exist_ok=True)
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
        help="send (default) | latest | open | list-channels",
    )
    p.add_argument(
        "channel",
        nargs="?",
        choices=sorted(CHANNELS),
        help="channel name (required for send/latest/open)",
    )
    p.add_argument("--from", dest="frm")
    p.add_argument("--to")
    p.add_argument("--body")
    p.add_argument("--project", default="workspace")
    p.add_argument("--status", default="open", choices=sorted(VALID_STATUS))
    p.add_argument("--in-reply-to")
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
    if cmd == "send" and channel is None:
        p.error("channel required for send")
    if cmd in ("latest", "open", "send") and channel is None:
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
    if cmd != "send":
        p.error(f"unknown command: {cmd}")

    if not a.frm or not a.to or a.body is None:
        p.error("send requires --from, --to, and --body")
    print(
        append_message(
            channel, a.frm, a.to, a.body, a.project, a.status, a.in_reply_to
        )
    )


if __name__ == "__main__":
    main()
