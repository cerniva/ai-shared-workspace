#!/usr/bin/env python3
"""Fail-closed integrity check for the shared handoff and append-only message files.

Run: python3 scripts/shared_state_integrity.py
"""
from __future__ import annotations

import json
from pathlib import Path

if __package__:
    from .handoff import validate
else:
    from handoff import validate

ROOT = Path(__file__).resolve().parents[1]
MESSAGE_FILES = {
    "messages/team-reports.md": "# Ortak ekip raporları",
    "messages/grok-to-chatgpt.md": "# Grok → ChatGPT",
}


class IntegrityError(ValueError):
    """A shared state file has been truncated, replaced, or made invalid."""


def check_message(path: Path, expected_heading: str) -> None:
    if not path.is_file():
        raise IntegrityError(f"{path}: missing shared message file")
    text = path.read_text(encoding="utf-8")
    if not text.startswith(expected_heading + "\n"):
        raise IntegrityError(f"{path}: missing original heading; possible overwrite")
    if len(text.strip()) <= len(expected_heading):
        raise IntegrityError(f"{path}: unexpectedly empty shared message archive")


def check_handoffs(path: Path) -> int:
    if not path.is_file():
        raise IntegrityError(f"{path}: missing handoff ledger")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise IntegrityError(f"{path}: expected JSON object")
        return validate(data)
    except (ValueError, TypeError, AttributeError, KeyError) as exc:
        raise IntegrityError(f"{path}: invalid handoff ledger: {exc}") from exc


def check_repo(root: Path = ROOT) -> int:
    for rel, heading in MESSAGE_FILES.items():
        check_message(root / rel, heading)
    return check_handoffs(root / "state/handoffs.json")


if __name__ == "__main__":
    try:
        count = check_repo()
        print(f"shared state valid; handoffs={count}")
    except IntegrityError as exc:
        raise SystemExit(f"integrity check failed: {exc}")
