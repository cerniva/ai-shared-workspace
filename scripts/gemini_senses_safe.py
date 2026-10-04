#!/usr/bin/env python3
"""Fail-closed wrapper for the Gemini worker.

Stable task IDs are idempotency keys. Historical completed blocks may coexist with
an accidentally re-enqueued active block. Reconcile those duplicates before the
provider call so an already completed task cannot spend another API request.
"""
from __future__ import annotations

import re
import runpy
from pathlib import Path

INBOX = Path("messages/inbox-gemini.md")
TASK_MARKER = re.compile(r"(?m)^## TASK[ \t]*$")
ACTIVE = {"queued", "ready", "open", "run"}


def field(block: str, name: str, default: str = "") -> str:
    match = re.search(rf"(?mi)^\s*{re.escape(name)}\s*:\s*(.*?)\s*$", block)
    return match.group(1).strip() if match else default


def task_blocks(text: str) -> list[tuple[int, int, str]]:
    marks = list(TASK_MARKER.finditer(text))
    return [
        (m.start(), marks[i + 1].start() if i + 1 < len(marks) else len(text),
         text[m.start(): marks[i + 1].start() if i + 1 < len(marks) else len(text)])
        for i, m in enumerate(marks)
    ]


def reconcile_completed_duplicates(text: str) -> tuple[str, list[str]]:
    blocks = task_blocks(text)
    completed_ids = {
        field(block, "id")
        for _, _, block in blocks
        if field(block, "id") and field(block, "status", "idle").lower() == "done"
    }
    replacements: list[tuple[int, int, str]] = []
    reconciled: list[str] = []
    for start, end, block in blocks:
        task_id = field(block, "id")
        status = field(block, "status", "idle").lower()
        if task_id not in completed_ids or status not in ACTIVE:
            continue
        updated = re.sub(
            r"(?mi)^(\s*status\s*:\s*)(queued|ready|open|run)(\s*)$",
            r"\1done\3",
            block,
            count=1,
        )
        replacements.append((start, end, updated))
        reconciled.append(task_id)

    for start, end, updated in reversed(replacements):
        text = text[:start] + updated + text[end:]
    return text, reconciled


def main() -> None:
    if not INBOX.exists():
        raise SystemExit("messages/inbox-gemini.md bulunamadı.")
    original = INBOX.read_text(encoding="utf-8")
    reconciled_text, ids = reconcile_completed_duplicates(original)
    if ids:
        INBOX.write_text(reconciled_text, encoding="utf-8")
        print("Reconciled completed duplicate Gemini task IDs: " + ", ".join(ids))
    runpy.run_path("scripts/gemini_senses.py", run_name="__main__")


if __name__ == "__main__":
    main()
