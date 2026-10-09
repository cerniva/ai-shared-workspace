#!/usr/bin/env python3
"""GitHub-file fallback channel between ChatGPT and Grok when Gmail is blocked.

A message is one JSON file under messages/fallback/<id>.json committed to the
repo. This module only writes/reads local files; it never pushes and never
claims delivery. "Delivered" means: the commit containing the file is on main
and the receiver wrote an ack (acked_by/acked_at) in a later commit.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANNEL = ROOT / "messages" / "fallback"
ACTORS = {"grok", "chatgpt", "auditor"}
ID_RE = re.compile(r"^FB-\d{8}-\d{6}-(grok|chatgpt|auditor)-[a-z0-9-]{1,40}$")
SECRET_RE = re.compile(r"(ghp_|github_pat_|sk-|xai-|AIza|Bearer\s+\S{12,}|-----BEGIN)", re.I)


class ChannelError(RuntimeError):
    pass


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def post(sender: str, to: str, subject: str, body: str, slug: str, channel: Path = CHANNEL, at: datetime | None = None) -> dict:
    if sender not in ACTORS or to not in ACTORS or sender == to:
        raise ChannelError("from/to must be different actors among grok, chatgpt, auditor")
    if not subject.strip() or not body.strip():
        raise ChannelError("subject and body are required")
    if SECRET_RE.search(subject + body):
        raise ChannelError("secret-like value rejected")
    at = at or datetime.now(timezone.utc)
    msg_id = f"FB-{at.strftime('%Y%m%d-%H%M%S')}-{sender}-{slug}"
    if not ID_RE.match(msg_id):
        raise ChannelError(f"invalid id {msg_id}")
    channel.mkdir(parents=True, exist_ok=True)
    path = channel / f"{msg_id}.json"
    if path.exists():
        raise ChannelError(f"{msg_id} already exists")
    msg = {"id": msg_id, "from": sender, "to": to, "subject": subject.strip(), "body": body.strip(),
           "created_at": at.replace(microsecond=0).isoformat(), "acked_by": None, "acked_at": None}
    text = json.dumps(msg, ensure_ascii=False, indent=2) + "\n"
    path.write_text(text, encoding="utf-8")
    if path.read_text(encoding="utf-8") != text:
        raise ChannelError("read-back mismatch")
    return msg


def load_all(channel: Path = CHANNEL) -> list[dict]:
    out = []
    for path in sorted(channel.glob("FB-*.json")):
        msg = json.loads(path.read_text(encoding="utf-8"))
        if msg.get("id") != path.stem or not ID_RE.match(path.stem):
            raise ChannelError(f"{path.name}: id mismatch")
        for key in ("from", "to", "subject", "body", "created_at"):
            if not msg.get(key):
                raise ChannelError(f"{path.name}: missing {key}")
        out.append(msg)
    return out


def inbox(actor: str, channel: Path = CHANNEL) -> list[dict]:
    return [m for m in load_all(channel) if m["to"] == actor and not m.get("acked_by")]


def ack(msg_id: str, actor: str, channel: Path = CHANNEL) -> dict:
    path = channel / f"{msg_id}.json"
    if not path.exists():
        raise ChannelError(f"unknown message {msg_id}")
    msg = json.loads(path.read_text(encoding="utf-8"))
    if msg["to"] != actor:
        raise ChannelError(f"only {msg['to']} can ack {msg_id}")
    if msg.get("acked_by"):
        return msg
    msg["acked_by"], msg["acked_at"] = actor, now()
    path.write_text(json.dumps(msg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return msg


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--channel", type=Path, default=CHANNEL)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("post")
    for f in ("from", "to", "subject", "body", "slug"):
        a.add_argument(f"--{f}", required=True)
    i = sub.add_parser("inbox")
    i.add_argument("actor")
    k = sub.add_parser("ack")
    k.add_argument("id")
    k.add_argument("--actor", required=True)
    sub.add_parser("validate")
    args = p.parse_args(argv)
    try:
        if args.cmd == "post":
            out = post(getattr(args, "from"), args.to, args.subject, args.body, args.slug, args.channel)
        elif args.cmd == "inbox":
            out = inbox(args.actor, args.channel)
        elif args.cmd == "ack":
            out = ack(args.id, args.actor, args.channel)
        else:
            out = {"valid": True, "messages": len(load_all(args.channel))}
    except ChannelError as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
