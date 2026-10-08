#!/usr/bin/env python3
"""Apply staged knowledge promotions to the canonical catalog and ledger.

Why: ChatGPT (write block) and Grok (connector must resend the whole 48 KB
catalog + 69 KB ledger in one call) can stage a small promotion file but
cannot safely rewrite the canonical JSON. This script, run by the
knowledge-promote workflow, merges every knowledge/promotions/*.json through
SourceCatalog.add / LearningLedger.add (dedup + read-back), so existing rows
are never dropped.

Promotion file shape (one or many):
  {"source": {...} | "sources": [...], "learning": {...} | "learnings": [...]}
Each staged source_id / learning_id must equal the ID the bridge computes;
otherwise the run fails closed and nothing is reported as persisted.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from knowledge_bridge import CatalogError, SourceCatalog
    from learning_bridge import LearningLedger, persistence_gate
except ModuleNotFoundError:  # Imported as scripts.knowledge_promote by tests.
    from scripts.knowledge_bridge import CatalogError, SourceCatalog
    from scripts.learning_bridge import LearningLedger, persistence_gate

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
    return gates


def apply_promotions(root: Path) -> dict[str, Any]:
    root = Path(root)
    catalog_path = root / "knowledge" / "source_catalog.json"
    ledger_path = root / "knowledge" / "learning_ledger.json"
    catalog = SourceCatalog(catalog_path)
    ledger = LearningLedger(ledger_path, catalog_path)
    report: dict[str, Any] = {"files": [], "sources_created": [], "learnings_created": []}
    for path in sorted((root / "knowledge" / "promotions").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            raise CatalogError(f"{path.name}: promotion must be a JSON object")
        sources = _items(doc, "source", "sources", path.name)
        learnings = _items(doc, "learning", "learnings", path.name)
        gates = _gates(doc, path.name)
        if not (sources or learnings or gates):
            raise CatalogError(f"{path.name}: promotion stages no source, learning or gate")
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
        report["files"].append(path.name)
    report["source_count"] = catalog.validate()
    report["learning_count"] = ledger.validate()
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
