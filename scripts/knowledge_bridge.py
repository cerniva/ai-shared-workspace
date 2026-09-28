from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Iterator
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


UTC = timezone.utc
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "knowledge" / "source_catalog.json"
REQUIRED_FIELDS = {
    "source_name",
    "canonical",
    "category",
    "purpose",
    "evidence_tier",
    "access_status",
    "cost_quota",
    "reliability_limits",
    "discovered_at",
    "provenance",
}
EVIDENCE_TIERS = {"official", "primary", "secondary", "community"}
ACCESS_STATUSES = {"verified-public", "verified-connected", "blocked", "unverified"}
PROVENANCE = {"verified", "user_reported", "unverified"}
TRACKING_PARAMS = {"gclid", "fbclid", "mc_cid", "mc_eid"}
SENSITIVE_QUERY_KEYS = {
    "access_token",
    "api_key",
    "apikey",
    "authorization",
    "key",
    "password",
    "secret",
    "token",
}
SECRET_PATTERNS = (
    re.compile(r"\b(?:sk|xai)-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{20,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{12,}={0,2}\b", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
EMAIL_PATTERN = re.compile(r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])")


class CatalogError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def canonicalize(value: str) -> str:
    value = value.strip()
    if not value:
        raise CatalogError("canonical source cannot be empty")
    if value.startswith("tool:"):
        return "tool:" + value[5:].strip().lower()
    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
        raise CatalogError("canonical must be an http(s) URL or tool:<id>")
    if parts.username or parts.password:
        raise CatalogError("credentials are forbidden in canonical URLs")
    query = []
    for key, item in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if lowered in SENSITIVE_QUERY_KEYS:
            raise CatalogError(f"sensitive query parameter forbidden: {key}")
        if lowered.startswith("utm_") or lowered in TRACKING_PARAMS:
            continue
        query.append((key, item))
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    if port and not ((scheme == "https" and port == 443) or (scheme == "http" and port == 80)):
        host = f"{host}:{port}"
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, host, path, urlencode(sorted(query)), ""))


def source_id(canonical: str) -> str:
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"src_{digest}"


def _assert_safe(record: dict[str, Any]) -> None:
    serialized = json.dumps(record, ensure_ascii=False)
    if EMAIL_PATTERN.search(serialized):
        raise CatalogError("personal email addresses are not allowed in the source catalog")
    for pattern in SECRET_PATTERNS:
        if pattern.search(serialized):
            raise CatalogError("secret-like value rejected")


def normalize_record(record: dict[str, Any]) -> dict[str, Any]:
    missing = sorted(REQUIRED_FIELDS - record.keys())
    if missing:
        raise CatalogError(f"missing required fields: {', '.join(missing)}")
    normalized = {key: str(record.get(key, "")).strip() for key in REQUIRED_FIELDS}
    normalized["canonical"] = canonicalize(normalized["canonical"])
    if normalized["evidence_tier"] not in EVIDENCE_TIERS:
        raise CatalogError("invalid evidence_tier")
    if normalized["access_status"] not in ACCESS_STATUSES:
        raise CatalogError("invalid access_status")
    if normalized["provenance"] not in PROVENANCE:
        raise CatalogError("invalid provenance")
    for field in REQUIRED_FIELDS - {"canonical"}:
        if not normalized[field]:
            raise CatalogError(f"{field} cannot be empty")
    normalized["source_id"] = source_id(normalized["canonical"])
    normalized["last_successful_use"] = str(record.get("last_successful_use") or "").strip() or None
    normalized["failure_note"] = str(record.get("failure_note") or "").strip() or None
    _assert_safe(normalized)
    return normalized


class SourceCatalog:
    def __init__(self, path: str | Path = DEFAULT_CATALOG):
        self.path = Path(path)

    def _lock_path(self) -> Path:
        return self.path.with_name(self.path.name + ".lock")

    @contextmanager
    def _locked(self) -> Iterator[None]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock_path().open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"schema_version": 1, "updated_at": None, "sources": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or not isinstance(data.get("sources"), list):
            raise CatalogError("invalid source catalog document")
        return data

    def _save(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("w", encoding="utf-8", dir=self.path.parent, delete=False) as tmp:
            json.dump(data, tmp, ensure_ascii=False, indent=2, sort_keys=True)
            tmp.write("\n")
            temp_path = Path(tmp.name)
        os.replace(temp_path, self.path)

    def add(self, record: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        candidate = normalize_record(record)
        with self._locked():
            data = self._load()
            for existing in data["sources"]:
                if existing.get("source_id") == candidate["source_id"] or existing.get("canonical") == candidate["canonical"]:
                    return existing, False
            data["sources"].append(candidate)
            data["sources"].sort(key=lambda item: item["source_id"])
            data["updated_at"] = utc_now()
            self._save(data)
            read_back = self._load()
            saved = next((item for item in read_back["sources"] if item["source_id"] == candidate["source_id"]), None)
            if saved != candidate:
                raise CatalogError("read-back verification failed")
            return saved, True

    def list(self) -> list[dict[str, Any]]:
        return self._load()["sources"]

    def find(self, value: str) -> dict[str, Any] | None:
        canonical = canonicalize(value) if not value.startswith("src_") else None
        for item in self.list():
            if item.get("source_id") == value or item.get("canonical") == canonical:
                return item
        return None

    def validate(self) -> int:
        data = self._load()
        seen_ids: set[str] = set()
        seen_canonical: set[str] = set()
        for item in data["sources"]:
            normalized = normalize_record(item)
            if item.get("source_id") != normalized["source_id"]:
                raise CatalogError(f"unstable source_id: {item.get('source_id')}")
            if normalized["source_id"] in seen_ids or normalized["canonical"] in seen_canonical:
                raise CatalogError("duplicate source entry")
            seen_ids.add(normalized["source_id"])
            seen_canonical.add(normalized["canonical"])
        return len(seen_ids)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Safe shared source catalog bridge")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    sub.add_parser("validate")
    find = sub.add_parser("find")
    find.add_argument("value")
    add = sub.add_parser("add")
    for field in sorted(REQUIRED_FIELDS):
        add.add_argument("--" + field.replace("_", "-"), required=True)
    add.add_argument("--last-successful-use")
    add.add_argument("--failure-note")
    return parser


def main() -> int:
    args = _parser().parse_args()
    catalog = SourceCatalog(args.catalog)
    if args.command == "list":
        result: Any = catalog.list()
    elif args.command == "find":
        result = catalog.find(args.value)
        if result is None:
            return 1
    elif args.command == "validate":
        result = {"valid": True, "source_count": catalog.validate()}
    else:
        payload = {field: getattr(args, field) for field in REQUIRED_FIELDS}
        payload["last_successful_use"] = args.last_successful_use
        payload["failure_note"] = args.failure_note
        record, created = catalog.add(payload)
        result = {"created": created, "record": record}
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
