"""Regression tests for the three staged promotion records in PR #141.

This test is deliberately confined to the existing PR branch and makes no
writes to the catalog, ledger, message archive, or main branch.
"""
from __future__ import annotations

import json
import os
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


    def test_imported_ids_exist_after_dry_run(self) -> None:
        """The PR gate must prove all staged IDs were actually imported."""
        if os.environ.get("PR141_REQUIRE_IMPORTED") != "1":
            self.skipTest("post-import verification only")
        expected_sources: dict[str, dict] = {}
        expected_learnings: dict[str, dict] = {}
        for name in NAMES:
            doc = json.loads((ROOT / "knowledge/promotions" / name).read_text(encoding="utf-8"))
            for row in entries(doc, "source", "sources"):
                self.assertNotIn(row["source_id"], expected_sources, "duplicate staged source")
                expected_sources[row["source_id"]] = row
            for row in entries(doc, "learning", "learnings"):
                self.assertNotIn(row["learning_id"], expected_learnings, "duplicate staged learning")
                expected_learnings[row["learning_id"]] = row
        catalog = json.loads((ROOT / "knowledge/source_catalog.json").read_text(encoding="utf-8"))
        ledger = json.loads((ROOT / "knowledge/learning_ledger.json").read_text(encoding="utf-8"))
        actual_sources = {row["source_id"]: row for row in catalog["sources"]}
        actual_learnings = {row["learning_id"]: row for row in ledger["learnings"]}
        self.assertFalse(expected_sources.keys() - actual_sources.keys(), "staged sources missing after import")
        self.assertFalse(expected_learnings.keys() - actual_learnings.keys(), "staged learnings missing after import")
        # An ID-only check can pass if a row with the correct ID has been
        # persisted with incomplete or altered decision/source metadata.
        for sid, staged in expected_sources.items():
            saved = actual_sources[sid]
            self.assertEqual(canonicalize(saved["canonical"]), canonicalize(staged["canonical"]))
            for field in ("source_name", "category", "purpose", "provenance",
                          "evidence_tier", "access_status"):
                self.assertEqual(saved[field], staged[field], f"{sid}: {field}")
        for lid, staged in expected_learnings.items():
            saved = actual_learnings[lid]
            for field in ("title", "domain", "claim", "decision", "evidence_status",
                          "provenance", "status"):
                self.assertEqual(saved[field], staged[field], f"{lid}: {field}")
            self.assertEqual(set(saved["source_ids"]), set(staged["source_ids"]), lid)
            self.assertEqual(set(saved["plan_tags"]), set(staged["plan_tags"]), lid)


    def test_import_preserves_existing_history(self) -> None:
        """A promotion must never delete, duplicate, or rewrite older rows."""
        if os.environ.get("PR141_REQUIRE_IMPORTED") != "1":
            self.skipTest("post-import preservation verification only")
        import subprocess

        for path, field, id_field in (
            ("knowledge/source_catalog.json", "sources", "source_id"),
            ("knowledge/learning_ledger.json", "learnings", "learning_id"),
        ):
            with self.subTest(path=path):
                # HEAD is the checked-out PR merge commit in CI, before the
                # scratch import changes working-tree files. Do not use a
                # hard-coded historical count; the main catalog can grow.
                baseline_text = subprocess.check_output(
                    ["git", "show", f"HEAD:{path}"],
                    cwd=ROOT, text=True,
                )
                baseline = json.loads(baseline_text)
                after = json.loads((ROOT / path).read_text(encoding="utf-8"))
                self.assertEqual(after["schema_version"], baseline["schema_version"])
                old_rows = baseline[field]
                new_rows = after[field]
                old_ids = [row[id_field] for row in old_rows]
                new_ids = [row[id_field] for row in new_rows]
                self.assertEqual(len(old_ids), len(set(old_ids)), "duplicate original IDs")
                self.assertEqual(len(new_ids), len(set(new_ids)), "duplicate imported IDs")
                saved = {row[id_field]: row for row in new_rows}
                for row in old_rows:
                    self.assertIn(row[id_field], saved, "historical record deleted")
                    self.assertEqual(saved[row[id_field]], row,
                                     f"historical record changed: {row[id_field]}")


if __name__ == "__main__":
    unittest.main()
