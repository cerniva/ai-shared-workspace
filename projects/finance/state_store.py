"""Finance runtime state: load -> dedup -> atomic write -> read-back (no blind overwrite).

save() takes the sha256 the caller loaded. If the file changed underneath
(another run wrote it), the mutation is re-applied once on the fresh copy;
a second change is a conflict and nothing is written. Every write is read
back and compared byte-for-byte before success is reported.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE = ROOT / "knowledge" / "finance_runtime_state.json"


class StateError(RuntimeError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dumps(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def validate(doc: Any) -> dict[str, int]:
    if not isinstance(doc, dict) or doc.get("schema_version") != 1:
        raise StateError("state must be an object with schema_version 1")
    counts: dict[str, int] = {}
    for key, id_field in (("sources", "source_id"), ("learnings", "learning_id")):
        rows = doc.get(key, [])
        if not isinstance(rows, list):
            raise StateError(f"{key} must be a list")
        ids = [row.get(id_field) for row in rows if isinstance(row, dict)]
        if len(ids) != len(rows) or any(not isinstance(i, str) or not i for i in ids):
            raise StateError(f"every {key} row needs a non-empty {id_field}")
        dupes = sorted({i for i in ids if ids.count(i) > 1})
        if dupes:
            raise StateError(f"duplicate {id_field}: {', '.join(dupes)}")
        counts[key] = len(ids)
    return counts


def load(path: Path = DEFAULT_STATE) -> tuple[dict[str, Any], str]:
    raw = Path(path).read_bytes()
    try:
        doc = json.loads(raw)
    except ValueError as exc:
        raise StateError(f"malformed JSON: {exc}") from exc
    validate(doc)
    return doc, digest(raw)


def upsert(rows: list[dict[str, Any]], row: dict[str, Any], id_field: str) -> bool:
    """Add a row unless its id exists; existing rows are never replaced or dropped."""
    if any(r.get(id_field) == row.get(id_field) for r in rows):
        return False
    rows.append(row)
    return True


def _write_atomic(path: Path, data: bytes) -> None:
    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False, prefix=f".{path.name}.") as tmp:
        tmp.write(data)
        tmp.flush()
        os.fsync(tmp.fileno())
    os.replace(tmp.name, path)


def save(path: Path, expected_sha: str, mutate: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    path = Path(path)
    for attempt in (1, 2):
        current, sha = load(path)
        if sha != expected_sha and attempt == 1:
            expected_sha = sha  # concurrent writer: re-apply once on the fresh copy
        elif sha != expected_sha:
            raise StateError("conflict: state changed twice during save; nothing written")
        before = {k: {r[f] for r in current.get(k, [])} for k, f in (("sources", "source_id"), ("learnings", "learning_id"))}
        mutate(current)
        validate(current)
        for k, f in (("sources", "source_id"), ("learnings", "learning_id")):
            lost = before[k] - {r[f] for r in current.get(k, [])}
            if lost:
                raise StateError(f"refusing to drop {k}: {sorted(lost)}")
        data = dumps(current)
        if load(path)[1] != expected_sha:
            continue
        _write_atomic(path, data)
        if path.read_bytes() != data:
            raise StateError("read-back mismatch after write")
        return {"sha256": digest(data), "attempt": attempt, "counts": validate(current)}
    raise StateError("conflict: state changed twice during save; nothing written")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["verify"])
    parser.add_argument("--path", type=Path, default=DEFAULT_STATE)
    args = parser.parse_args(argv)
    try:
        doc, sha = load(args.path)
        print(json.dumps({"status": "PASS", "sha256": sha, "counts": validate(doc)}))
        return 0
    except (OSError, StateError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
