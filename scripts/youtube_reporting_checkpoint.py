"""Offline, fail-closed YouTube Reporting createdAfter decision consumer.

This module never calls YouTube, writes a checkpoint, or claims channel access.
A caller must independently verify durable imports and apply the proposed cursor.
PayoutLens is out of scope.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.knowledge_bridge import CatalogError, SourceCatalog, DEFAULT_CATALOG
from scripts.learning_bridge import LearningLedger, DEFAULT_LEDGER

LEARNING_ID = "learn_0bdcee93377fd18d"
SOURCE_ID = "src_be6523a27c85e346"
GATE = "REPORT_CREATED_AFTER_ACK_GATE"


def _time(value: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError("INVALID_CREATE_TIME")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("INVALID_CREATE_TIME") from exc
    if parsed.tzinfo is None:
        raise ValueError("INVALID_CREATE_TIME: timezone required")
    return parsed.astimezone(timezone.utc)


def read_policy(ledger_path: str | Path = DEFAULT_LEDGER,
                catalog_path: str | Path = DEFAULT_CATALOG) -> dict[str, str]:
    ledger = LearningLedger(ledger_path, catalog_path)
    matches = [row for row in ledger.for_plan("system")
               if row.get("learning_id") == LEARNING_ID]
    if len(matches) != 1 or matches[0].get("evidence_status") != "verified":
        raise CatalogError("bridge_failure: active system checkpoint learning missing")
    row = matches[0]
    if GATE not in row.get("decision", "") or SOURCE_ID not in row.get("source_ids", []):
        raise CatalogError("bridge_failure: checkpoint policy/source mismatch")
    source = SourceCatalog(catalog_path).find(SOURCE_ID)
    if not source or source.get("evidence_tier") != "official":
        raise CatalogError("bridge_failure: official checkpoint source missing")
    return {"learning_id": LEARNING_ID, "source_id": SOURCE_ID}


def evaluate_batch(batch: dict[str, Any],
                   ledger_path: str | Path = DEFAULT_LEDGER,
                   catalog_path: str | Path = DEFAULT_CATALOG) -> dict[str, Any]:
    """Return a proposed checkpoint, never a committed checkpoint.

    The caller must provide a *complete* paginated report list and independent
    durable read-back acknowledgements. This is not an ingestion implementation.
    """
    policy = read_policy(ledger_path, catalog_path)
    if not isinstance(batch, dict) or not isinstance(batch.get("reports"), list):
        raise ValueError("INVALID_BATCH")
    previous = batch.get("previous_checkpoint")
    previous_dt = _time(previous) if previous is not None else None
    selected: dict[tuple[str, str, str], tuple[datetime, dict]] = {}
    seen_ids: dict[str, str] = {}
    for report in batch["reports"]:
        if not isinstance(report, dict):
            raise ValueError("INVALID_REPORT")
        try:
            rid = report["id"]
            job = report["jobId"]
            start = report["startTime"]
            end = report["endTime"]
            created = _time(report["createTime"])
        except (KeyError, TypeError) as exc:
            raise ValueError("INVALID_REPORT") from exc
        if not all(isinstance(v, str) and v for v in (rid, job, start, end)):
            raise ValueError("INVALID_REPORT")
        if _time(start) >= _time(end):
            raise ValueError("INVALID_PERIOD")
        fingerprint = json.dumps({k: report[k] for k in ("id", "jobId", "startTime", "endTime", "createTime")}, sort_keys=True)
        if rid in seen_ids:
            if seen_ids[rid] != fingerprint:
                raise ValueError("CONFLICTING_REPORT_ID")
            continue
        seen_ids[rid] = fingerprint
        key = (job, start, end)
        old = selected.get(key)
        if old is None or created > old[0]:
            selected[key] = (created, report)
        elif created == old[0] and rid != old[1]["id"]:
            raise ValueError("AMBIGUOUS_BACKFILL")
    winners = [pair[1] for pair in selected.values()]
    unacked = sorted(row["id"] for row in winners
                     if row.get("import_status") != "persisted_readback_verified")
    complete = batch.get("pagination_complete") is True
    index_verified = batch.get("batch_index_readback_verified") is True
    if not complete:
        status = "HOLD_INCOMPLETE_PAGINATION"
    elif unacked or not index_verified:
        status = "HOLD_UNVERIFIED_IMPORT"
    elif not winners:
        status = "NO_NEW_REPORTS"
    else:
        status = "ADVANCE_READY"
    candidate = max((stamp for stamp, _ in selected.values()), default=None)
    if status == "ADVANCE_READY" and previous_dt and candidate <= previous_dt:
        status = "NO_NEW_REPORTS"
    proposed = (candidate.isoformat().replace("+00:00", "Z")
                if status == "ADVANCE_READY" else previous)
    return {
        "decision_status": status,
        "decision_before": {"createdAfter": previous},
        "decision_after_proposed": {"createdAfter": proposed},
        "checkpoint_committed": False,
        "selected_report_ids": sorted(row["id"] for row in winners),
        "unverified_report_ids": unacked,
        "applied_learning_ids": [policy["learning_id"]],
        "source_ids": [policy["source_id"]],
        "production_channel_access": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Propose, never commit, a Reporting API checkpoint.")
    parser.add_argument("batch_json", type=Path)
    args = parser.parse_args()
    result = evaluate_batch(json.loads(args.batch_json.read_text(encoding="utf-8")))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
