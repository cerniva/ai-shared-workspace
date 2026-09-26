#!/usr/bin/env python3
"""Route the oldest actionable chatgpt-to-gemini letter not yet in the inbox.

The workflow listens to both the letter file and inbox; this routes messages
into the worker queue without skipping older open letters.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LETTER = ROOT / "messages" / "chatgpt-to-gemini.md"
INBOX = ROOT / "messages" / "inbox-gemini.md"
ACTIONABLE = {"open", "queued", "ready", "run"}
_SPLIT = re.compile(r"(?m)^---\s*$")


def parse_blocks(text: str) -> list[dict[str, str]]:
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


def actionable_letters(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return [
        block for block in parse_blocks(path.read_text(encoding="utf-8"))
        if block.get("status", "").lower() in ACTIONABLE
    ]


def inbox_already_has(mid: str) -> bool:
    if not INBOX.exists() or not mid:
        return False
    pattern = re.compile(rf"(?m)^id:[ \\t]*{re.escape(mid)}[ \\t]*$")
    return bool(pattern.search(INBOX.read_text(encoding="utf-8")))


def route() -> str:
    letters = actionable_letters(LETTER)
    letter = next((item for item in letters if not inbox_already_has(item.get("id", ""))), None)
    if not letter:
        if letters:
            return f"noop:already-routed:{letters[0].get('id', '')}"
        return "noop:no-actionable-letter"
    mid = letter["id"]
    prompt = letter.get("body") or ""
    task = (
        "\n## TASK\n"
        f"status: queued\n"
        f"id: {mid}\n"
        f"from: {letter.get('from', 'chatgpt')}\n"
        f"to: gemini\n"
        f"source_channel: chatgpt-to-gemini\n"
        f"created_at: {letter.get('created_at', '')}\n"
        f"project: {letter.get('project', 'workspace')}\n"
        f"prompt: |\n"
        f"  {prompt.replace(chr(10), chr(10) + '  ')}\n"
    )
    INBOX.parent.mkdir(parents=True, exist_ok=True)
    if INBOX.exists():
        INBOX.write_text(INBOX.read_text(encoding="utf-8") + task, encoding="utf-8")
    else:
        INBOX.write_text("# Inbox → Gemini API\n" + task, encoding="utf-8")
    try:
        sys.path.insert(0, str(ROOT))
        from scripts import desk_bridge as db

        db.mark_delivery("chatgpt-to-gemini", mid, "pending")
    except Exception:
        pass
    return f"routed:{mid}"


def main() -> int:
    print(route())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
