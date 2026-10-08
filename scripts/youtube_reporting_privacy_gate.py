"""Read a persisted Reporting API privacy rule before aggregating authorized CSV.

This consumer is opt-in: it never downloads channel data or modifies the ledgers.
PayoutLens is out of scope. Only aggregate counts are returned.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, SourceCatalog, DEFAULT_CATALOG
from scripts.learning_bridge import LearningLedger, DEFAULT_LEDGER

LEARNING_ID = "learn_607a11f5b569ffa0"
SOURCE_ID = "src_be6523a27c85e346"
GATE = "REPORT_PRIVACY_SUPPRESSION_GATE"
SUPPRESSED = {
    "trafficSourceDetail": {"NULL"},
    "ageGroup": {"NULL"},
    "gender": {"NULL"},
    "subscribedStatus": {"NULL"},
    "country": {"ZZ"},
    "province": {"US-ZZ"},
}


def read_rule(
    ledger_path: str | Path = DEFAULT_LEDGER,
    catalog_path: str | Path = DEFAULT_CATALOG,
) -> dict:
    """Fail closed if the exact learning and its official source cannot be read."""
    ledger = LearningLedger(ledger_path, catalog_path)
    record = ledger.find(LEARNING_ID)
    if not record or GATE not in record.get("decision", ""):
        raise CatalogError("bridge_failure: canonical privacy learning not available")
    if record.get("evidence_status") != "verified" or SOURCE_ID not in record.get("source_ids", []):
        raise CatalogError("bridge_failure: learning evidence/source mismatch")
    source = SourceCatalog(catalog_path).find(SOURCE_ID)
    if not source or source.get("evidence_tier") != "official":
        raise CatalogError("bridge_failure: official source not readable")
    return {"learning_id": LEARNING_ID, "source_id": SOURCE_ID, "gate": GATE}


def summarize_csv(
    csv_text: str,
    ledger_path: str | Path = DEFAULT_LEDGER,
    catalog_path: str | Path = DEFAULT_CATALOG,
) -> dict:
    """Aggregate a single report's views without dropping privacy-suppressed rows.

    Rows from different reports or backfills must not be concatenated blindly.
    This is not a replacement for a complete report-ingestion pipeline.
    """
    evidence = read_rule(ledger_path, catalog_path)
    if not csv_text.strip():
        raise ValueError("INVALID_EMPTY_FILE")
    reader = csv.DictReader(io.StringIO(csv_text))
    columns = reader.fieldnames
    if not columns or len(columns) != len(set(columns)) or "views" not in columns:
        raise ValueError("INVALID_HEADER")
    if any(not name or name != name.strip() for name in columns):
        raise ValueError("INVALID_HEADER")

    total = suppressed_total = rows = suppressed_rows = 0
    for row in reader:
        if None in row or any(value is None for value in row.values()):
            raise ValueError("INVALID_ROW_WIDTH")
        raw_views = row["views"]
        if not raw_views.isascii() or not raw_views.isdecimal():
            raise ValueError("INVALID_VIEWS")
        views = int(raw_views)
        hidden = any(row.get(field) in markers for field, markers in SUPPRESSED.items())
        total += views
        rows += 1
        if hidden:
            suppressed_total += views
            suppressed_rows += 1
    return {
        **evidence,
        "status": "VALID_NO_DATA" if rows == 0 else "VALID_DATA",
        "rows": rows,
        "total_views": total,
        "privacy_suppressed_rows": suppressed_rows,
        "privacy_suppressed_views": suppressed_total,
        "production_channel_access": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a local authorized Reporting API CSV.")
    parser.add_argument("csv_path", type=Path)
    args = parser.parse_args()
    print(json.dumps(summarize_csv(args.csv_path.read_text(encoding="utf-8")), sort_keys=True))


if __name__ == "__main__":
    main()
