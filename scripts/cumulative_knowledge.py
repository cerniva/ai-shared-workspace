"""Read-only cumulative knowledge snapshot for Finance, Video/Shopify and System.

Preserves all source/learning rows and historical supersessions. It does not
modify the canonical ledgers, call external APIs, or claim plan consumption.
PayoutLens is out of scope.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.knowledge_bridge import CatalogError, DEFAULT_CATALOG, SourceCatalog
from scripts.learning_bridge import DEFAULT_LEDGER, LearningLedger

PLANS = ("finance", "video_shopify", "system")
COMMON_DOMAINS = {
    "workspace-knowledge", "repository-concurrency", "identity-integration-security",
}
ALLOWED_STATUSES = {"active", "superseded", "inactive"}


def _routes(item: dict[str, Any]) -> tuple[str, ...]:
    """Explicit plan tags win; legacy domains use conservative routing."""
    tags = item.get("plan_tags")
    if tags is not None:
        if not isinstance(tags, list) or any(tag not in PLANS for tag in tags):
            raise CatalogError("invalid plan_tags for " + str(item.get("learning_id")))
        return tuple(sorted(set(tags)))
    domain = str(item.get("domain") or "").lower()
    if domain in COMMON_DOMAINS:
        return PLANS
    if domain.startswith(("youtube", "shopify")):
        return ("video_shopify",)
    if domain.startswith(("finance", "macro", "market", "crypto", "investment")):
        return ("finance",)
    if domain.startswith(("repository", "workspace", "system", "worker", "automation", "identity")):
        return ("system",)
    return ()


def _status(item: dict[str, Any], superseded_ids: set[str]) -> str:
    value = item.get("status")
    if value is not None and value not in ALLOWED_STATUSES:
        raise CatalogError("invalid status for " + str(item.get("learning_id")))
    if value in {"inactive", "superseded"} or item.get("outcome") == "invalidated":
        return value if value in {"inactive", "superseded"} else "inactive"
    if item["learning_id"] in superseded_ids:
        return "superseded"
    return "active"


def load_current_knowledge(
    catalog_path: str | Path = DEFAULT_CATALOG,
    ledger_path: str | Path = DEFAULT_LEDGER,
    root: str | Path | None = None,
) -> dict[str, Any]:
    """Validate, load, classify and retain ALL canonical records.

    Snapshot is read-only; consumer evidence and usage counts require a separate
    write/read-back transaction and must not be inferred from this result.
    """
    catalog = SourceCatalog(catalog_path)
    ledger = LearningLedger(ledger_path, catalog_path)
    source_count = catalog.validate()
    learning_count = ledger.validate()
    sources = catalog.list()
    learnings = ledger.list()
    if len(sources) != source_count or len(learnings) != learning_count:
        raise CatalogError("PERSISTENCE_FAILURE: inconsistent snapshot counts")
    by_source = {row["source_id"]: row for row in sources}
    by_learning = {row["learning_id"]: row for row in learnings}
    if len(by_source) != len(sources) or len(by_learning) != len(learnings):
        raise CatalogError("PERSISTENCE_FAILURE: duplicate stable ID")
    for row in learnings:
        if not set(row["source_ids"]).issubset(by_source):
            raise CatalogError("bridge_failure: unresolved source reference")
    superseded_ids = {
        row["supersedes"] for row in learnings
        if row.get("supersedes") and row.get("evidence_status") == "verified"
        and row.get("status", "active") == "active"
        and row.get("outcome") != "invalidated"
    }
    statuses = {row["learning_id"]: _status(row, superseded_ids) for row in learnings}
    active = [row for row in learnings if statuses[row["learning_id"]] == "active"]
    historical = [row for row in learnings if statuses[row["learning_id"]] != "active"]
    plans = {}
    unrouted = []
    for row in active:
        if not _routes(row):
            unrouted.append(row["learning_id"])
    for plan in PLANS:
        selected = [row for row in active if plan in _routes(row)]
        refs = sorted({sid for row in selected for sid in row["source_ids"]})
        plans[plan] = {
            "learning_ids": [row["learning_id"] for row in selected],
            "source_ids": refs,
            "learnings": selected,
            "sources": [by_source[sid] for sid in refs],
        }
    # Preserve full records, including failure/fallback histories. A missing
    # optional usage field is UNKNOWN, never implicitly 0.
    base = Path(root) if root is not None else Path(__file__).resolve().parents[1]
    overlays = {}
    optional = {
        "research_router": "knowledge/RESEARCH_ROUTER.md",
        "video_learning_pool": "knowledge/video-production-learning-pool.md",
        "finance_runtime": "knowledge/finance_runtime_state.json",
        "connection_state": "state/now.json",
        "cross_chat_sync": "state/cross_chat_sync.json",
    }
    for key, rel in optional.items():
        path = base / rel
        if path.is_file():
            overlays[key] = {
                "path": rel,
                "content": json.loads(path.read_text(encoding="utf-8"))
                if path.suffix == ".json" else path.read_text(encoding="utf-8"),
                "access_status": "read_from_repository_snapshot_not_live_verified",
            }
        else:
            overlays[key] = {"path": rel, "access_status": "missing"}
    return {
        "source_count": len(sources),
        "learning_count": len(learnings),
        "active_learning_count": len(active),
        "historical_learning_count": len(historical),
        "sources": sources,
        "learnings": learnings,
        "active_learnings": active,
        "historical_learnings": historical,
        "derived_status": statuses,
        "plans": plans,
        "unrouted_learning_ids": unrouted,
        "overlays": overlays,
        "usage_evidence": "not_verified_by_read_only_loader",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only cumulative knowledge snapshot")
    parser.add_argument("--plan", choices=PLANS)
    args = parser.parse_args()
    snapshot = load_current_knowledge()
    summary = {
        "source_count": snapshot["source_count"],
        "learning_count": snapshot["learning_count"],
        "active_learning_count": snapshot["active_learning_count"],
        "historical_learning_count": snapshot["historical_learning_count"],
        "unrouted_learning_ids": snapshot["unrouted_learning_ids"],
        "overlays": {key: val["access_status"] for key, val in snapshot["overlays"].items()},
        "usage_evidence": snapshot["usage_evidence"],
    }
    if args.plan:
        summary["plan"] = args.plan
        summary["learning_ids"] = snapshot["plans"][args.plan]["learning_ids"]
        summary["source_ids"] = snapshot["plans"][args.plan]["source_ids"]
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
