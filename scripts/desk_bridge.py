#!/usr/bin/env python3
"""File-desk bridge: append protocol-safe agent handoffs without rewriting history."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = {
    "grok-to-chatgpt": (ROOT / "messages" / "grok-to-chatgpt.md", "grok", "chatgpt"),
    "chatgpt-to-grok": (ROOT / "messages" / "chatgpt-to-grok.md", "chatgpt", "grok"),
    "inbox-gemini": (ROOT / "messages" / "inbox-gemini.md", None, "gemini"),
    "gemini-to-chatgpt": (ROOT / "messages" / "gemini-to-chatgpt.md", "gemini", "chatgpt"),
}
VALID_STATUS = {"open", "done", "blocked", "queued"}

def now_tr() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))

def make_id(agent: str) -> str:
    return f"MSG-{now_tr().strftime('%Y%m%d-%H%M%S')}-{agent}-bridge"

def append_message(channel: str, frm: str, to: str, body: str,
                   project: str = "workspace", status: str = "open",
                   in_reply_to: str | None = None) -> str:
    path, expected_from, expected_to = CHANNELS[channel]
    lines = body.strip().splitlines()
    if not lines or len(lines) > 12:
        raise ValueError("body must contain 1..12 lines")
    if status not in VALID_STATUS:
        raise ValueError(f"invalid status: {status}")
    if expected_from and frm != expected_from:
        raise ValueError(f"{channel} requires from={expected_from}")
    if to != expected_to:
        raise ValueError(f"{channel} requires to={expected_to}")
    mid = make_id(frm)
    created = now_tr().isoformat(timespec="seconds")
    block = ["", "---", f"id: {mid}", f"from: {frm}", f"to: {to}",
             f"in_reply_to: {in_reply_to or 'null'}", f"created_at: {created}",
             f"project: {project}", f"status: {status}", "---", "", body.strip(), ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write("\n".join(block))
    return mid

def main() -> None:
    p = argparse.ArgumentParser(description="Append one protocol-safe desk message")
    p.add_argument("channel", choices=sorted(CHANNELS))
    p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--project", default="workspace")
    p.add_argument("--status", default="open", choices=sorted(VALID_STATUS))
    p.add_argument("--in-reply-to")
    a = p.parse_args()
    print(append_message(a.channel, a.frm, a.to, a.body, a.project, a.status, a.in_reply_to))

if __name__ == "__main__":
    main()
