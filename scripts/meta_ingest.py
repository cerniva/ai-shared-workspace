#!/usr/bin/env python3
"""Append a Meta desk message to messages/from-meta.md. No secrets in body."""
from __future__ import annotations

import base64
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "messages" / "from-meta.md"

SECRETISH = re.compile(
    r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{16,}"
    r"|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----)",
    re.I,
)


def decode_body() -> str:
    raw_b64 = (os.environ.get("META_BODY_B64") or "").strip()
    if raw_b64:
        pad = "=" * ((4 - len(raw_b64) % 4) % 4)
        return base64.b64decode(raw_b64 + pad).decode("utf-8", errors="replace")
    return os.environ.get("META_BODY") or ""


def main() -> int:
    body = decode_body().strip()
    source = (os.environ.get("META_SOURCE") or "dispatch").strip()[:80]
    if not body:
        print("empty body; skip")
        return 0
    if SECRETISH.search(body):
        print("refused: body looks like a secret")
        return 2
    if len(body) > 20000:
        body = body[:20000] + "\n\n[truncated]"

    now = datetime.now(timezone(timedelta(hours=3)))
    stamp = now.strftime("%Y%m%d-%H%M%S")
    iso = now.strftime("%Y-%m-%dT%H:%M:%S+03:00")
    msg_id = f"MSG-{stamp}-meta-ingest"
    block = (
        f"\n---\n"
        f"id: {msg_id}\n"
        f"from: meta\n"
        f"to: team\n"
        f"in_reply_to: null\n"
        f"created_at: {iso}\n"
        f"project: workspace\n"
        f"status: open\n"
        f"source: {source}\n"
        f"---\n\n"
        f"intent: meta-ingest | info\n"
        f"evidence: ingested via GitHub Action (no Meta git identity).\n"
        f"decision: treat as Meta write on desk.\n"
        f"next-action: ChatGPT/Grok poll and apply if reversible.\n"
        f"blocker_if_any: none\n\n"
        f"```\n{body}\n```\n"
    )
    existing = OUT.read_text(encoding="utf-8") if OUT.exists() else "# from-meta\n"
    OUT.write_text(existing.rstrip() + "\n" + block, encoding="utf-8")
    print(f"wrote {msg_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
