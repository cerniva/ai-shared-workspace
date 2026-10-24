"""Regression tests for the three staged promotion records in PR #141.

This test is deliberately confined to the existing PR branch and makes no
writes to the catalog, ledger, message archive, or main branch.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.knowledge_bridge import canonicalize, source_id
from scripts.learning_bridge import learning_id

ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "2026-10-10-0827-rest-ruleset-archive-gate.json",
    "2026-10-10-1127-github-rest-pagination-completeness.json",
    "2026-10-10-2127-required-check-event-gate.json",
)


def entries(doc: dict, singular: str, plural: str) -> list[dict]:
    return ([doc[singular]] if singular in doc else []) + list(doc.get(plural, []))


class PR141PromotionGate(unittest.TestCase):
    def test_schema_identity_references_and_gates(self) -> None:
        catalog = json.loads((ROOT / "knowledge/source_catalog.json").read_text(encoding="utf-8"))
        ledger = json.loads((ROOT / "knowledge/learning_ledger.json").read_text(encoding="utf-8"))
        known_sources = {s["source_id"]: s for s in catalog["sources"]}
        known_learnings = {l["learning_id"]: l for l in ledger["learnings"]}
        staged_sources: set[str] = set()
        staged_learnings: set[str] = set()
        canonical_urls: set[str] = set()
        learning_rows: list[dict] = []
        for name in NAMES:
            with self.subTest(file=name):
                doc = json.loads((ROOT / "knowledge/promotions" / name).read_text(encoding="utf-8"))
                self.assertEqual(doc.get("schema_version"), 1)
                gates = doc.get("gates", [])
                self.assertTrue(gates)
                sources = entries(doc, "source", "sources")
                learnings = entries(doc, "learning", "learnings")
                self.assertTrue(sources and learnings)
                for source in sources:
                    canonical = canonicalize(source["canonical"])
                    sid = source_id(canonical)
                    self.assertEqual(source["source_id"], sid)
                    self.assertNotIn(sid, staged_sources)
                    self.assertNotIn(canonical, canonical_urls)
                    if sid in known_sources:
                        self.assertEqual(canonicalize(known_sources[sid]["canonical"]), canonical)
                    staged_sources.add(sid)
                    canonical_urls.add(canonical)
                for learning in learnings:
                    lid = learning_id(learning["domain"], learning["claim"])
                    self.assertEqual(learning["learning_id"], lid)
                    self.assertNotIn(lid, staged_learnings)
                    self.assertEqual(learning.get("status"), "active")
                    self.assertIn("system", learning.get("plan_tags", []))
                    self.assertTrue(learning.get("source_ids"))
                    for gate in gates:
                        self.assertIn(gate, learning.get("decision", ""))
                    if lid in known_learnings:
                        saved = known_learnings[lid]
                        self.assertEqual(saved["domain"], learning["domain"])
                        self.assertEqual(saved["claim"], learning["claim"])
                        self.assertEqual(set(saved["source_ids"]), set(learning["source_ids"]))
                    staged_learnings.add(lid)
                    learning_rows.append(learning)
        self.assertEqual((len(staged_sources), len(staged_learnings)), (4, 3))
        # A successful promotion later adds these IDs to main. Re-running this
        # gate after import must remain idempotent, not reject persisted rows.
        for learning in learning_rows:
            self.assertFalse(set(learning["source_ids"]) - (set(known_sources) | staged_sources))


if __name__ == "__main__":
    unittest.main()
