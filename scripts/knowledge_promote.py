#!/usr/bin/env python3
"""Apply staged knowledge promotions to the canonical catalog and ledger.

Why: ChatGPT (write block) and Grok (connector must resend the whole 48 KB
catalog + 69 KB ledger in one call) can stage a small promotion file but
cannot safely rewrite the canonical JSON. This script, run by the
knowledge-promote workflow, merges every knowledge/promotions/*.json through
SourceCatalog.add / LearningLedger.add (dedup + read-back), so existing rows
are never dropped.

Promotion file shape (one or many):
  {"source": {...} | "sources": [...], "learning": {...} | "learnings": [...],
   "source_refreshes": [{"source_id": "src_...", "verified_at": "<iso8601+tz>"}]}
Each staged source_id / learning_id must equal the ID the bridge computes;
otherwise the run fails closed and nothing is reported as persisted.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:
    from scripts.knowledge_bridge import CatalogError, SourceCatalog, _assert_safe, canonicalize, source_id
    from scripts.learning_bridge import LearningLedger, learning_id, persistence_gate
    from scripts.knowledge_freshness import refresh_source
except ModuleNotFoundError:  # Direct script execution from scripts/.
    from knowledge_bridge import CatalogError, SourceCatalog, _assert_safe, canonicalize, source_id
    from learning_bridge import LearningLedger, learning_id, persistence_gate
    from knowledge_freshness import refresh_source

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATHS = ("knowledge/source_catalog.json", "knowledge/learning_ledger.json")
COMMIT_MESSAGE = "knowledge-promote: merge staged promotions into canonical ledger"


def _items(doc: dict[str, Any], single: str, plural: str, name: str = "promotion") -> list[dict[str, Any]]:
    """Return staged items; fail closed on any malformed shape.

    Previously a non-dict "source"/"learning", a non-list "sources"/"learnings"
    or a non-dict list element was silently skipped, so the run still reported
    success while the staged row was never persisted (silent data loss).
    """
    items: list[dict[str, Any]] = []
    if single in doc and doc[single] is not None:
        if not isinstance(doc[single], dict):
            raise CatalogError(f"{name}: '{single}' must be an object, got {type(doc[single]).__name__}")
        items.append(doc[single])
    if plural in doc and doc[plural] is not None:
        if not isinstance(doc[plural], list):
            raise CatalogError(f"{name}: '{plural}' must be a list, got {type(doc[plural]).__name__}")
        for index, entry in enumerate(doc[plural]):
            if not isinstance(entry, dict):
                raise CatalogError(f"{name}: '{plural}[{index}]' must be an object, got {type(entry).__name__}")
            items.append(entry)
    return items


def _gates(doc: dict[str, Any], name: str = "promotion") -> list[str]:
    gates = doc.get("gates")
    if gates is None:
        gates = []
    if not isinstance(gates, list) or not all(isinstance(g, str) and g.strip() for g in gates):
        raise CatalogError(f"{name}: 'gates' must be a list of non-empty strings")
    gates = list(gates)
    validators = doc.get("validators")
    if validators is not None and not isinstance(validators, dict):
        raise CatalogError(f"{name}: 'validators' must be an object")
    if isinstance(validators, dict) and "gate" in validators:
        gate = validators["gate"]
        if not isinstance(gate, str) or not gate.strip():
            raise CatalogError(f"{name}: 'validators.gate' must be a non-empty string")
        gates.append(gate)
    for gate in gates:
        _assert_safe({"gate": gate})
    return gates


PROMOTION_SCHEMA_VERSION = 1


def _ids(path: Path, key: str, id_field: str) -> set[str]:
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {row[id_field] for row in data.get(key, []) if isinstance(row, dict) and id_field in row}


def _snapshot(catalog_path: Path, ledger_path: Path) -> dict[str, set[str]]:
    return {
        "sources": _ids(catalog_path, "sources", "source_id"),
        "learnings": _ids(ledger_path, "learnings", "learning_id"),
    }


def _check_superset(before: dict[str, set[str]], after: dict[str, set[str]]) -> None:
    """Integrity rule 3/7: a promotion may only add rows, never drop one."""
    for kind in ("sources", "learnings"):
        lost = sorted(before[kind] - after[kind])
        if lost:
            raise CatalogError(f"integrity: {kind} would be lost: {', '.join(lost[:5])}")


def _atomic_copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", dir=dst.parent, delete=False, prefix=f".{dst.name}.") as handle:
        handle.write(src.read_bytes())
        handle.flush()
        os.fsync(handle.fileno())
        tmp = Path(handle.name)
    os.replace(tmp, dst)


@contextmanager
def _canonical_locks(*paths: Path) -> Iterator[None]:
    """Hold the same <file>.lock flocks SourceCatalog/LearningLedger.add use.

    Integrity rule 6: without this, a concurrent add() between our snapshot
    and the scratch copy-over was silently overwritten (lost update, shown by
    tests/test_knowledge_race.py). Fixed order (catalog, ledger) avoids
    deadlock between two batches.
    """
    handles = []
    try:
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = path.with_name(path.name + ".lock").open("a+", encoding="utf-8")
            handles.append(handle)
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        yield
    finally:
        for handle in reversed(handles):
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            handle.close()


def apply_promotions(root: Path) -> dict[str, Any]:
    root = Path(root)
    with _canonical_locks(root / "knowledge" / "source_catalog.json", root / "knowledge" / "learning_ledger.json"):
        return _apply_promotions_locked(root)


def _apply_promotions_locked(root: Path) -> dict[str, Any]:
    """Apply every promotion as one all-or-nothing batch (integrity spec 2026-10-10).

    The whole batch runs first against a scratch copy of the catalog + ledger.
    Any error (schema, staged id, dangling source, duplicate, secret, missing
    gate) aborts before the canonical files are touched. Only when the scratch
    result keeps every existing id is it copied over the canonical files and
    read back byte-for-byte.
    """
    root = Path(root)
    catalog_path = root / "knowledge" / "source_catalog.json"
    ledger_path = root / "knowledge" / "learning_ledger.json"
    before = _snapshot(catalog_path, ledger_path)
    with tempfile.TemporaryDirectory(prefix="knowledge-promote-") as scratch:
        work = Path(scratch)
        work_catalog = work / "source_catalog.json"
        work_ledger = work / "learning_ledger.json"
        for real, copy in ((catalog_path, work_catalog), (ledger_path, work_ledger)):
            if real.exists():
                shutil.copyfile(real, copy)
        report = _apply_batch(root / "knowledge" / "promotions", work_catalog, work_ledger)
        _check_superset(before, _snapshot(work_catalog, work_ledger))
        changed = []
        for real, copy in ((catalog_path, work_catalog), (ledger_path, work_ledger)):
            if copy.exists() and (not real.exists() or real.read_bytes() != copy.read_bytes()):
                _atomic_copy(copy, real)
                changed.append(real.name)
            if copy.exists() and real.read_bytes() != copy.read_bytes():
                raise CatalogError(f"integrity: read-back mismatch for {real.name}")
    report["changed_files"] = changed
    report["source_count"] = SourceCatalog(catalog_path).validate()
    report["learning_count"] = LearningLedger(ledger_path, catalog_path).validate()
    if report["source_count"] < len(before["sources"]) or report["learning_count"] < len(before["learnings"]):
        raise CatalogError("integrity: canonical counts decreased")
    return report


def _apply_batch(promotions_dir: Path, catalog_path: Path, ledger_path: Path) -> dict[str, Any]:
    catalog = SourceCatalog(catalog_path)
    ledger = LearningLedger(ledger_path, catalog_path)
    report: dict[str, Any] = {"files": [], "sources_created": [], "learnings_created": []}
    seen_sources: dict[str, str] = {}
    seen_learnings: dict[str, str] = {}
    for path in sorted(promotions_dir.glob("*.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise CatalogError(f"{path.name}: malformed JSON: {exc}") from exc
        if not isinstance(doc, dict):
            raise CatalogError(f"{path.name}: promotion must be a JSON object")
        if "schema_version" in doc and doc["schema_version"] != PROMOTION_SCHEMA_VERSION:
            raise CatalogError(f"{path.name}: schema_version {doc['schema_version']!r} != {PROMOTION_SCHEMA_VERSION}")
        sources = _items(doc, "source", "sources", path.name)
        learnings = _items(doc, "learning", "learnings", path.name)
        gates = _gates(doc, path.name)
        refreshes = _items(doc, "source_refresh", "source_refreshes", path.name)
        for ref in refreshes:
            if not str(ref.get("source_id") or "").startswith("src_") or not ref.get("verified_at"):
                raise CatalogError(f"{path.name}: source_refresh needs source_id and verified_at")
        if not (sources or learnings or gates or refreshes):
            raise CatalogError(f"{path.name}: promotion stages no source, learning, gate or refresh")
        # Reject a staged id before any local write. add() persists the bridge
        # id immediately; checking afterwards left the computed row on disk.
        for src in sources:
            staged = src.get("source_id")
            if staged:
                expected = source_id(canonicalize(str(src.get("canonical") or "")))
                if staged != expected:
                    raise CatalogError(f"{path.name}: staged source_id {staged} != {expected}")
        for item in learnings:
            staged = item.get("learning_id")
            if staged:
                expected = learning_id(str(item.get("domain") or ""), str(item.get("claim") or ""))
                if staged != expected:
                    raise CatalogError(f"{path.name}: staged learning_id {staged} != {expected}")
        # Integrity rule: the same id staged with different content in two
        # files is ambiguous; fail instead of letting file order pick a winner.
        for kind, rows, seen, make in (
            ("source", sources, seen_sources, lambda r: source_id(canonicalize(str(r.get("canonical") or "")))),
            ("learning", learnings, seen_learnings, lambda r: learning_id(str(r.get("domain") or ""), str(r.get("claim") or ""))),
        ):
            for row in rows:
                key = make(row)
                body = json.dumps({k: v for k, v in row.items() if k not in ("source_id", "learning_id")}, sort_keys=True, ensure_ascii=False)
                if key in seen and seen[key] != body:
                    raise CatalogError(f"{path.name}: duplicate {kind} {key} staged with different content")
                seen[key] = body
        for src in sources:
            saved, created = catalog.add(src)
            staged = src.get("source_id")
            if staged and staged != saved["source_id"]:
                raise CatalogError(f"{path.name}: staged source_id {staged} != {saved['source_id']}")
            if created:
                report["sources_created"].append(saved["source_id"])
        for item in learnings:
            payload = {k: v for k, v in item.items() if k != "learning_id"}
            saved, created = ledger.add(payload)
            staged = item.get("learning_id")
            if staged and staged != saved["learning_id"]:
                raise CatalogError(f"{path.name}: staged learning_id {staged} != {saved['learning_id']}")
            if created:
                report["learnings_created"].append(saved["learning_id"])
        for gate in gates:
            persistence_gate(ledger, gate)
        for ref in refreshes:
            if refresh_source(catalog, str(ref["source_id"]), str(ref["verified_at"])):
                report.setdefault("sources_refreshed", []).append(ref["source_id"])
        report["files"].append(path.name)
    catalog.validate()
    ledger.validate()
    return report


def _run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def publish(repo: Path, attempts: int = 4) -> dict[str, Any]:
    _run(["git", "config", "user.name", "knowledge-promote-bot"], repo)
    _run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], repo)
    last = "not-started"
    for attempt in range(1, attempts + 1):
        _run(["git", "fetch", "origin", "main"], repo)
        _run(["git", "reset", "--hard", "origin/main"], repo)
        report = apply_promotions(repo)
        _run(["git", "add", *CANONICAL_PATHS], repo)
        dirty = _run(["git", "diff", "--cached", "--quiet"], repo, check=False)
        if dirty.returncode == 0:
            report["result"] = "noop"
            return report
        _run(["git", "commit", "-m", COMMIT_MESSAGE], repo)
        push = _run(["git", "push", "origin", "HEAD:main"], repo, check=False)
        if push.returncode == 0:
            report["result"] = "pushed"
            report["commit"] = _run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
            return report
        last = (push.stderr or push.stdout or "push rejected").strip()
        print(f"knowledge-promote attempt {attempt} rejected: {last}", file=sys.stderr)
    raise RuntimeError(f"knowledge-promote push failed after {attempts} attempts: {last}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["apply", "publish"])
    parser.add_argument("--repo", default=os.environ.get("KNOWLEDGE_PROMOTE_REPO", str(ROOT)))
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    report = apply_promotions(repo) if args.command == "apply" else publish(repo)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # fail closed, never report persisted
        print(f"knowledge-promote failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
