"""Fail-closed structural checks for append-only message archives."""
from __future__ import annotations

import re

RECORD_ID = re.compile(r"^id:\s*(\S.*?)\s*$")


def missing_record_delimiters(text: str) -> list[int]:
    """Return 1-based line numbers of record IDs lacking their opening --- line."""
    lines = text.splitlines()
    return [i + 1 for i, line in enumerate(lines)
            if RECORD_ID.match(line) and (i == 0 or lines[i - 1].strip() != "---")]


def assert_record_delimiters(text: str, path: str) -> None:
    missing = missing_record_delimiters(text)
    if missing:
        raise ValueError(f"{path}: missing record delimiter before id at lines {missing[:10]}")
