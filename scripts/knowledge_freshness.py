#!/usr/bin/env python3
"""Freshness check for the knowledge library.

Lists catalog sources whose last verification (``last_successful_use``; falls back
to ``discovered_at``) is older than --max-age-days (default 30), plus learnings
older than that. With --reverify it fetches each stale http(s) source and, for
every success, stages a ``source_refreshes`` promotion file under
knowledge/promotions/ so knowledge_promote.py advances the timestamp through the
normal all-or-nothing promotion path. The canonical catalog/ledger are never
written by this script. Failures are only reported.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

# scripts.X olarak import edildiyse daima paket yolunu kullan: scripts/ sys.path'te olsa bile
# knowledge_bridge iki kez (bare + scripts.) yüklenip CatalogError sınıfı ikiye bölünmesin.
if __package__ == "scripts":
    from scripts.knowledge_bridge import CatalogError, SourceCatalog
else:
    from knowledge_bridge import CatalogError, SourceCatalog

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = ROOT / "knowledge" / "source_catalog.json"
DEFAULT_LEDGER = ROOT / "knowledge" / "learning_ledger.json"
DEFAULT_PROMOTIONS = ROOT / "knowledge" / "promotions"
UA = "cerniva-knowledge-freshness/1.0 (+https://github.com/cerniva/ai-shared-workspace)"
UTC = timezone.utc

Fetcher = Callable[[str], int]


def _parse(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=UTC)


def last_verified(row: dict[str, Any]) -> datetime | None:
    return _parse(row.get("last_successful_use")) or _parse(row.get("discovered_at"))


def stale_sources(sources: list[dict[str, Any]], now: datetime, max_age_days: int) -> list[dict[str, Any]]:
    cutoff = now - timedelta(days=max_age_days)
    out = []
    for row in sources:
        seen = last_verified(row)
        if seen is None or seen < cutoff:
            out.append(row)
    return out


def stale_learnings(learnings: list[dict[str, Any]], now: datetime, max_age_days: int) -> list[dict[str, Any]]:
    cutoff = now - timedelta(days=max_age_days)
    return [r for r in learnings if (_parse(r.get("learned_at")) or now) < cutoff]


def default_fetch(url: str, timeout: float = 20.0) -> int:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - catalog URLs are http(s) only
            resp.read(2048)
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception:  # noqa: BLE001 - network failure is a report, not a crash
        return 0


def reverify(rows: list[dict[str, Any]], fetch: Fetcher, now: datetime) -> tuple[list[dict[str, str]], list[dict[str, Any]]]:
    refreshed: list[dict[str, str]] = []
    failed: list[dict[str, Any]] = []
    stamp = now.astimezone(UTC).replace(microsecond=0).isoformat()
    for row in rows:
        url = str(row.get("canonical") or "")
        if not url.startswith(("http://", "https://")):
            failed.append({"source_id": row.get("source_id"), "reason": "not-fetchable"})
            continue
        status = fetch(url)
        if 200 <= status < 400:
            refreshed.append({"source_id": row["source_id"], "verified_at": stamp})
        else:
            failed.append({"source_id": row.get("source_id"), "url": url, "status": status})
    return refreshed, failed


def write_promotion(refreshed: list[dict[str, str]], promotions_dir: Path, now: datetime) -> Path | None:
    if not refreshed:
        return None
    promotions_dir.mkdir(parents=True, exist_ok=True)
    path = promotions_dir / f"freshness-{now.astimezone(UTC):%Y-%m-%d}.json"
    doc = {"schema_version": 1, "source_refreshes": refreshed}
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def refresh_source(catalog: SourceCatalog, source_id_value: str, verified_at: str) -> bool:
    """Advance last_successful_use of an existing catalog source (used by knowledge_promote).

    Only that one field changes and only forward in time, so replaying an old
    refresh promotion is a no-op. Unknown ids and naive timestamps fail closed.
    """
    stamp = _parse(verified_at) if "T" in str(verified_at) else None
    if stamp is None or datetime.fromisoformat(str(verified_at).replace("Z", "+00:00")).tzinfo is None:
        raise CatalogError("refresh verified_at must be ISO-8601 with a timezone")
    with catalog._locked():  # same flock SourceCatalog.add uses
        data = catalog._load()
        row = next((item for item in data["sources"] if item.get("source_id") == source_id_value), None)
        if row is None:
            raise CatalogError(f"refresh: unknown source_id {source_id_value}")
        current = _parse(row.get("last_successful_use"))
        if current is not None and current >= stamp:
            return False
        row["last_successful_use"] = stamp.astimezone(UTC).replace(microsecond=0).isoformat()
        data["updated_at"] = datetime.now(UTC).replace(microsecond=0).isoformat()
        catalog._save(data)
        return True


def run(*, catalog: Path = DEFAULT_CATALOG, ledger: Path = DEFAULT_LEDGER, promotions: Path = DEFAULT_PROMOTIONS,
        max_age_days: int = 30, do_reverify: bool = False, fetch: Fetcher = default_fetch,
        now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(UTC)
    sources = json.loads(Path(catalog).read_text(encoding="utf-8")).get("sources", [])
    learnings = json.loads(Path(ledger).read_text(encoding="utf-8")).get("learnings", []) if Path(ledger).exists() else []
    stale = stale_sources(sources, now, max_age_days)
    report: dict[str, Any] = {
        "checked_at": now.astimezone(UTC).replace(microsecond=0).isoformat(),
        "max_age_days": max_age_days,
        "stale_sources": [{"source_id": r.get("source_id"), "canonical": r.get("canonical"),
                           "last_verified": (last_verified(r).isoformat() if last_verified(r) else None)} for r in stale],
        "stale_learnings": [r.get("learning_id") for r in stale_learnings(learnings, now, max_age_days)],
    }
    if do_reverify:
        refreshed, failed = reverify(stale, fetch, now)
        path = write_promotion(refreshed, Path(promotions), now)
        report.update(refreshed=[r["source_id"] for r in refreshed], failed=failed,
                      promotion=str(path.relative_to(ROOT)) if path and path.is_relative_to(ROOT) else (str(path) if path else None))
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--max-age-days", type=int, default=30)
    p.add_argument("--reverify", action="store_true", help="fetch stale URLs and stage a refresh promotion")
    p.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    p.add_argument("--promotions", default=str(DEFAULT_PROMOTIONS))
    a = p.parse_args(argv)
    report = run(catalog=Path(a.catalog), ledger=Path(a.ledger), promotions=Path(a.promotions),
                 max_age_days=a.max_age_days, do_reverify=a.reverify)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
