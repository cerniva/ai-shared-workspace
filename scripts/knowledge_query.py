#!/usr/bin/env python3
"""Free-text search over knowledge/learning_ledger.json and knowledge/source_catalog.json.

Read-only. Filters:
  topic -> substring of learning ``domain`` / source ``category``
  plan  -> learning ``plan_tags`` (finance | video_shopify | system); sources match
           when a learning with that plan cites them
  tag   -> exact match on any label: plan_tags, domain, category, evidence_tier,
           evidence_status, provenance, outcome
Usable as ``from scripts.knowledge_query import query_knowledge`` or as a CLI.
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LEDGER = ROOT / "knowledge" / "learning_ledger.json"
DEFAULT_CATALOG = ROOT / "knowledge" / "source_catalog.json"

LEARNING_TEXT = ("title", "claim", "decision", "next_measurement", "domain")
SOURCE_TEXT = ("source_name", "purpose", "reliability_limits", "category", "canonical")
_TR = str.maketrans({"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
                     "ç": "c", "Ç": "c", "ö": "o", "Ö": "o", "ü": "u", "Ü": "u"})


def _norm(text: str) -> str:
    text = str(text or "").translate(_TR).lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9_]+", _norm(text)) if len(t) > 1]


def _load(path: Path, key: str) -> list[dict[str, Any]]:
    if not Path(path).exists():
        return []
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = data.get(key, [])
    return [r for r in rows if isinstance(r, dict)]


def _score(row: dict[str, Any], fields: Iterable[str], terms: list[str]) -> int:
    if not terms:
        return 1
    score = 0
    for field in fields:
        hay = _norm(row.get(field, ""))
        weight = 3 if field in ("title", "source_name") else 1
        for term in terms:
            if term in hay:
                score += weight
    # every term must appear somewhere
    blob = " ".join(_norm(row.get(f, "")) for f in fields)
    return score if all(t in blob for t in terms) else 0


def _labels(row: dict[str, Any]) -> set[str]:
    out = {_norm(t) for t in row.get("plan_tags", []) or []}
    for key in ("domain", "category", "evidence_tier", "evidence_status", "provenance", "outcome"):
        if row.get(key):
            out.add(_norm(row[key]))
    return out


def query_knowledge(text: str = "", *, topic: str | None = None, plan: str | None = None,
                    tag: str | None = None, kind: str = "all", limit: int = 10,
                    ledger_path: Path | str = DEFAULT_LEDGER,
                    catalog_path: Path | str = DEFAULT_CATALOG) -> list[dict[str, Any]]:
    """Return ranked hits: ``{"kind", "id", "title", "score", "url"|"source_ids", "snippet"}``."""
    if kind not in ("all", "learning", "source"):
        raise ValueError("kind must be all, learning or source")
    terms = _tokens(text)
    learnings = _load(Path(ledger_path), "learnings")
    sources = _load(Path(catalog_path), "sources")
    topic_n = _norm(topic) if topic else None
    plan_n = _norm(plan) if plan else None
    tag_n = _norm(tag) if tag else None
    plan_sources: set[str] = set()
    if plan_n:
        for row in learnings:
            if plan_n in {_norm(t) for t in row.get("plan_tags", []) or []}:
                plan_sources.update(row.get("source_ids", []) or [])

    hits: list[dict[str, Any]] = []
    if kind in ("all", "learning"):
        for row in learnings:
            if topic_n and topic_n not in _norm(row.get("domain", "")):
                continue
            if plan_n and plan_n not in {_norm(t) for t in row.get("plan_tags", []) or []}:
                continue
            if tag_n and tag_n not in _labels(row):
                continue
            score = _score(row, LEARNING_TEXT, terms)
            if score:
                hits.append({"kind": "learning", "id": row.get("learning_id"), "title": row.get("title", ""),
                             "score": score, "source_ids": row.get("source_ids", []),
                             "snippet": str(row.get("claim", ""))[:280]})
    if kind in ("all", "source"):
        for row in sources:
            if topic_n and topic_n not in _norm(row.get("category", "")):
                continue
            if plan_n and row.get("source_id") not in plan_sources:
                continue
            if tag_n and tag_n not in _labels(row):
                continue
            score = _score(row, SOURCE_TEXT, terms)
            if score:
                hits.append({"kind": "source", "id": row.get("source_id"), "title": row.get("source_name", ""),
                             "score": score, "url": row.get("canonical", ""),
                             "snippet": str(row.get("purpose", ""))[:280]})
    hits.sort(key=lambda h: (-h["score"], h["kind"], str(h["id"])))
    return hits[: max(0, int(limit))]


def format_hits(hits: list[dict[str, Any]]) -> str:
    if not hits:
        return "Bilgi kütüphanesinde eşleşme bulunamadı."
    lines = []
    for h in hits:
        ref = h.get("url") or ", ".join(h.get("source_ids", []))
        lines.append(f"• [{h['kind']}] {h['title']} ({h['id']})\n  {h['snippet']}\n  ↳ {ref}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("text", nargs="*", help="free-text query")
    p.add_argument("--topic")
    p.add_argument("--plan")
    p.add_argument("--tag")
    p.add_argument("--kind", default="all", choices=["all", "learning", "source"])
    p.add_argument("--limit", type=int, default=10)
    p.add_argument("--json", action="store_true")
    p.add_argument("--ledger", default=str(DEFAULT_LEDGER))
    p.add_argument("--catalog", default=str(DEFAULT_CATALOG))
    a = p.parse_args(argv)
    hits = query_knowledge(" ".join(a.text), topic=a.topic, plan=a.plan, tag=a.tag, kind=a.kind,
                           limit=a.limit, ledger_path=a.ledger, catalog_path=a.catalog)
    print(json.dumps(hits, ensure_ascii=False, indent=2) if a.json else format_hits(hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
