#!/usr/bin/env python3
"""Load ledger learnings tagged for one plan so a plan runner actually uses them.

Wraps LearningLedger.for_plan: returns only active rows explicitly tagged for
the plan (finance, video_shopify, system or a display alias). A missing or
invalid ledger never blocks the runner; it is reported in ``error`` so the run
log shows the learning loop was not available.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.knowledge_bridge import CatalogError
from scripts.learning_bridge import DEFAULT_CATALOG, DEFAULT_LEDGER, LearningLedger


def plan_learnings(
    tag: str,
    *,
    ledger_path: Path = DEFAULT_LEDGER,
    catalog_path: Path = DEFAULT_CATALOG,
) -> dict[str, Any]:
    try:
        rows = LearningLedger(ledger_path, catalog_path).for_plan(tag)
    except (CatalogError, OSError, ValueError) as exc:
        return {"tag": tag, "count": 0, "learnings": [], "error": str(exc)}
    active = [row for row in rows if row.get("status", "active") == "active"]
    learnings = [
        {
            "learning_id": row["learning_id"],
            "title": row["title"],
            "decision": row["decision"],
            "source_ids": list(row.get("source_ids") or []),
        }
        for row in active
    ]
    return {"tag": tag, "count": len(learnings), "learnings": learnings, "error": None}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("tag")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    args = parser.parse_args(argv)
    report = plan_learnings(args.tag, ledger_path=args.ledger, catalog_path=args.catalog)
    text = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(f"plan_learnings tag={report['tag']} count={report['count']} error={report['error']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
