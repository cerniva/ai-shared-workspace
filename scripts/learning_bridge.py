from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterator

try:
    from knowledge_bridge import CatalogError, SourceCatalog, _assert_safe
except ModuleNotFoundError:  # Imported as scripts.learning_bridge by the test suite.
    from scripts.knowledge_bridge import CatalogError, SourceCatalog, _assert_safe


UTC = timezone.utc
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "knowledge" / "learning_ledger.json"
DEFAULT_CATALOG = ROOT / "knowledge" / "source_catalog.json"
EVIDENCE_STATUSES = {"verified", "mixed", "user-reported", "unverified"}
OUTCOMES = {"applied", "validated", "pending", "invalidated"}
PROVENANCE = {"verified", "user_reported", "unverified"}
REQUIRED_FIELDS = {
    "title",
    "domain",
    "claim",
    "evidence_status",
    "decision",
    "outcome",
    "next_measurement",
    "learned_at",
    "provenance",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def learning_id(domain: str, claim: str) -> str:
    key = json.dumps(
        {"domain": domain.strip().lower(), "claim": " ".join(claim.split()).lower()},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return "learn_" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]


def normalize_learning(record: dict[str, Any], valid_source_ids: set[str]) -> dict[str, Any]:
    missing = sorted(REQUIRED_FIELDS - record.keys())
    if missing:
        raise CatalogError(f"missing required fields: {', '.join(missing)}")
    normalized = {field: str(record.get(field, "")).strip() for field in REQUIRED_FIELDS}
    for field, value in normalized.items():
        if not value:
            raise CatalogError(f"{field} cannot be empty")
    if normalized["evidence_status"] not in EVIDENCE_STATUSES:
        raise CatalogError("invalid evidence_status")
    if normalized["outcome"] not in OUTCOMES:
        raise CatalogError("invalid outcome")
    if normalized["provenance"] not in PROVENANCE:
        raise CatalogError("invalid provenance")

    source_ids = record.get("source_ids")
    if not isinstance(source_ids, list) or not source_ids:
        raise CatalogError("source_ids must be a non-empty list")
    normalized_ids = sorted({str(value).strip() for value in source_ids if str(value).strip()})
    unknown = sorted(set(normalized_ids) - valid_source_ids)
    if unknown:
        raise CatalogError(f"unknown source_ids: {', '.join(unknown)}")

    for field in ("failure_history", "fallback_history"):
        value = record.get(field, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise CatalogError(f"{field} must be a list of strings")
        normalized[field] = [item.strip() for item in value if item.strip()]

    normalized["source_ids"] = normalized_ids
    normalized["supersedes"] = str(record.get("supersedes") or "").strip() or None
    normalized["learning_id"] = learning_id(normalized["domain"], normalized["claim"])
    _assert_safe(normalized)
    return normalized


class LearningLedger:
    def __init__(
        self,
        path: str | Path = DEFAULT_LEDGER,
        source_catalog_path: str | Path = DEFAULT_CATALOG,
    ):
        self.path = Path(path)
        self.source_catalog_path = Path(source_catalog_path)

    def _source_ids(self) -> set[str]:
        return {item["source_id"] for item in SourceCatalog(self.source_catalog_path).list()}

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_name(self.path.name + ".lock")
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "updated_at": None, "learnings": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or not isinstance(data.get("learnings"), list):
            raise CatalogError("invalid learning ledger document")
        return data

    def _save(self, data: dict[str, Any]) -> None:
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2, sort_keys=True)
            tmp.write("\n")
            temp_path = Path(tmp.name)
        os.replace(temp_path, self.path)

    def add(self, record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        candidate = normalize_learning(record, self._source_ids())
        with self._locked():
            data = self._load()
            for existing in data["learnings"]:
                if existing.get("learning_id") == candidate["learning_id"]:
                    return existing, False
            if candidate["supersedes"]:
                known_ids = {item.get("learning_id") for item in data["learnings"]}
                if candidate["supersedes"] not in known_ids:
                    raise CatalogError("supersedes references an unknown learning_id")
            data["learnings"].append(candidate)
            data["learnings"].sort(key=lambda item: item["learning_id"])
            data["updated_at"] = utc_now()
            self._save(data)
            saved = next(
                item for item in self._load()["learnings"]
                if item["learning_id"] == candidate["learning_id"]
            )
            if saved != candidate:
                raise CatalogError("learning read-back verification failed")
            return saved, True

    def list(self) -> list[dict[str, Any]]:
        return self._load()["learnings"]

    def find(self, value: str) -> dict[str, Any] | None:
        for item in self.list():
            if item.get("learning_id") == value:
                return item
        return None

    def validate(self) -> int:
        data = self._load()
        valid_sources = self._source_ids()
        seen: set[str] = set()
        ordered_ids = {item.get("learning_id") for item in data["learnings"]}
        for item in data["learnings"]:
            normalized = normalize_learning(item, valid_sources)
            if item.get("learning_id") != normalized["learning_id"]:
                raise CatalogError(f"unstable learning_id: {item.get('learning_id')}")
            if normalized["learning_id"] in seen:
                raise CatalogError("duplicate learning entry")
            if normalized["supersedes"] and normalized["supersedes"] not in ordered_ids:
                raise CatalogError("unknown supersedes target")
            seen.add(normalized["learning_id"])
        return len(seen)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe shared learning ledger bridge")
    parser.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    sub.add_parser("validate")
    find = sub.add_parser("find")
    find.add_argument("learning_id")
    add = sub.add_parser("add")
    for field in sorted(REQUIRED_FIELDS):
        add.add_argument("--" + field.replace("_", "-"), required=True)
    add.add_argument("--source-id", action="append", dest="source_ids", required=True)
    add.add_argument("--failure", action="append", dest="failure_history", default=[])
    add.add_argument("--fallback", action="append", dest="fallback_history", default=[])
    add.add_argument("--supersedes")
    return parser


def main() -> int:
    args = _parser().parse_args()
    ledger = LearningLedger(args.ledger, args.catalog)
    if args.command == "list":
        result: Any = ledger.list()
    elif args.command == "find":
        result = ledger.find(args.learning_id)
        if result is None:
            return 1
    elif args.command == "validate":
        result = {"valid": True, "learning_count": ledger.validate()}
    else:
        payload = {field: getattr(args, field) for field in REQUIRED_FIELDS}
        payload.update(
            source_ids=args.source_ids,
            failure_history=args.failure_history,
            fallback_history=args.fallback_history,
            supersedes=args.supersedes,
        )
        item, created = ledger.add(payload)
        result = {"created": created, "record": item}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
