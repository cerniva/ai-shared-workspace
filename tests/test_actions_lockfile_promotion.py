"""Validate the staged Actions lockfile learning without rewriting shared history."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import normalize_record
from scripts.learning_bridge import normalize_learning
from scripts.knowledge_promote import apply_promotions

ROOT = Path(__file__).resolve().parents[1]
PROMO = ROOT / "knowledge/promotions/2026-10-27-github-actions-lockfile-review.json"
SOURCE_ID = "src_f5fa4d6131d7db33"
SECONDARY_SOURCE_ID = "src_76811b880217b4a5"
LEARNING_ID = "learn_a381f47f8f318363"
GATE = "ACTIONS_DEPENDENCY_LOCKFILE_REVIEW_GATE"


class ActionsLockfilePromotionTests(unittest.TestCase):
    def test_schema_identity_and_non_duplicate_main(self):
        doc = json.loads(PROMO.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(doc["gates"], [GATE])
        source = normalize_record(doc["source"])
        secondary_source = normalize_record(doc["sources"][0])
        learning = normalize_learning(doc["learning"], {SOURCE_ID, SECONDARY_SOURCE_ID})
        self.assertEqual(source["source_id"], SOURCE_ID)
        self.assertEqual(secondary_source["source_id"], SECONDARY_SOURCE_ID)
        self.assertEqual(learning["learning_id"], LEARNING_ID)
        self.assertEqual(learning["source_ids"], sorted([SOURCE_ID, SECONDARY_SOURCE_ID]))
        self.assertIn("never hand-edit", learning["decision"])
        self.assertIn("internal transitive dependencies", learning["decision"])
        self.assertEqual(learning["plan_tags"], ["system"])
        self.assertIn(GATE, learning["decision"])
        self.assertIn("REVIEW_ONLY", learning["decision"])

        catalog = json.loads((ROOT / "knowledge/source_catalog.json").read_text())
        ledger = json.loads((ROOT / "knowledge/learning_ledger.json").read_text())
        same_urls = [row for row in catalog["sources"] if row["canonical"] == source["canonical"]]
        secondary_urls = [row for row in catalog["sources"] if row["canonical"] == secondary_source["canonical"]]
        same_ids = [row for row in ledger["learnings"] if row["learning_id"] == LEARNING_ID]
        self.assertLessEqual(len(same_urls), 1)
        self.assertLessEqual(len(secondary_urls), 1)
        self.assertLessEqual(len(same_ids), 1)
        if same_urls:
            self.assertEqual(same_urls[0]["source_id"], SOURCE_ID)
        if secondary_urls:
            self.assertEqual(secondary_urls[0]["source_id"], SECONDARY_SOURCE_ID)
        if same_ids:
            self.assertEqual(same_ids[0]["claim"], learning["claim"])

    def test_atomic_scratch_promotion_preserves_history_and_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            promotions = root / "knowledge/promotions"
            promotions.mkdir(parents=True)
            for name in ("source_catalog.json", "learning_ledger.json"):
                shutil.copyfile(ROOT / "knowledge" / name, root / "knowledge" / name)
            shutil.copyfile(PROMO, promotions / PROMO.name)
            before_sources = {row["source_id"] for row in
                json.loads((root / "knowledge/source_catalog.json").read_text())["sources"]}
            before_learnings = {row["learning_id"] for row in
                json.loads((root / "knowledge/learning_ledger.json").read_text())["learnings"]}
            report = apply_promotions(root)
            after_sources = {row["source_id"] for row in
                json.loads((root / "knowledge/source_catalog.json").read_text())["sources"]}
            after_learnings = {row["learning_id"] for row in
                json.loads((root / "knowledge/learning_ledger.json").read_text())["learnings"]}
            self.assertTrue(before_sources <= after_sources)
            self.assertTrue(before_learnings <= after_learnings)
            self.assertIn(SOURCE_ID, after_sources)
            self.assertIn(SECONDARY_SOURCE_ID, after_sources)
            self.assertIn(LEARNING_ID, after_learnings)
            self.assertIn(PROMO.name, report["files"])
            # Replaying the same staged promotion must not create a new
            # source/learning, rewrite the ledgers, or discard history.
            catalog_path = root / "knowledge/source_catalog.json"
            ledger_path = root / "knowledge/learning_ledger.json"
            catalog_bytes = catalog_path.read_bytes()
            ledger_bytes = ledger_path.read_bytes()
            again = apply_promotions(root)
            self.assertEqual(again["sources_created"], [])
            self.assertEqual(again["learnings_created"], [])
            self.assertEqual(again["changed_files"], [])
            self.assertEqual(catalog_path.read_bytes(), catalog_bytes)
            self.assertEqual(ledger_path.read_bytes(), ledger_bytes)


if __name__ == "__main__":
    unittest.main()
