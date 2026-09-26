#!/usr/bin/env python3
"""File-desk bridge: append a protocol message without rewriting history."""
from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANNELS = {
    "grok-to-chatgpt": ROOT / "messages" / "grok-to-chatgpt.md",
    "chatgpt-to-grok": ROOT / "messages" / "chatgpt-to-grok.md",
    "inbox-gemini": ROOT / "messages" / "inbox-gemini.md",
    "gemini-to-chatgpt": ROOT / "messages" / "gemini-to-chatgpt.md",
}


def now_tr() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=3)))


def make_id(agent: str) -> str:
    stamp = now_tr().strftime("%Y%m%d-%H%M%S")
    return f"MSG-{stamp}-{agent}-bridge"


def append_message(
    channel: str,
    frm: str,
    to: str,
    body: str,
    project: str = "workspace",
    status: str = "open",
    in_reply_to: str | None = None,
) -> str:
    path = CHANNELS[channel]
    mid = make_id(frm)
    created = now_tr().strftime("%Y-%m-%dT%H:%M:%S+03:00")
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


def main() -> None:
    p = argparse.ArgumentParser(description="Append a desk message")
    p.add_argument("channel", choices=sorted(CHANNELS))
    p.add_argument("--from", dest="frm", required=True)
    p.add_argument("--to", required=True)
    p.add_argument("--body", required=True)
    p.add_argument("--project", default="workspace")
    p.add_argument("--status", default="open")
    p.add_argument("--in-reply-to", default=None)
    args = p.parse_args()
    mid = append_message(
        args.channel,
        args.frm,
        args.to,
        args.body,
        args.project,
        args.status,
        args.in_reply_to,
    )
    print(mid)


if __name__ == "__main__":
    main()
