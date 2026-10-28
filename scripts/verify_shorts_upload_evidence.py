#!/usr/bin/env python3
"""Verify downloaded Shorts upload evidence before use; fail closed on SHA mismatch.

This is a read-only artifact consumer. It never publishes, merges, or updates main.
"""
import argparse
import hashlib
import re
from pathlib import Path

EXPECTED = {"upload_ledger.json", "upload_result.json"}


def verify(folder: Path) -> None:
    manifest = folder / "SHA256SUMS"
    lines = manifest.read_text(encoding="utf-8").splitlines()
    if len(lines) != len(EXPECTED):
        raise ValueError("missing or extra evidence hash entries")
    found = set()
    for line in lines:
        match = re.fullmatch(r"([0-9a-f]{64})  (upload_ledger\.json|upload_result\.json)", line)
        if match is None:
            raise ValueError("invalid SHA256SUMS entry")
        digest, filename = match.groups()
        if filename in found:
            raise ValueError("duplicate SHA256SUMS entry")
        found.add(filename)
        actual = hashlib.sha256((folder / filename).read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError("artifact digest mismatch: " + filename)
    if found != EXPECTED:
        raise ValueError("incomplete upload evidence")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    args = parser.parse_args()
    try:
        verify(args.folder)
    except (OSError, ValueError) as exc:
        print("EVIDENCE_BLOCKED: " + str(exc))
        return 3
    print("EVIDENCE_VERIFIED: upload_ledger.json + upload_result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
