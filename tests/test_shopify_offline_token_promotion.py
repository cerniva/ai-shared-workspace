"""Additive, idempotent promotion regression for Shopify public-app offline-token gate.

This test only mutates temporary ledger copies; never the canonical main files.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_promote import apply_promotions
from scripts.knowledge_bridge import SourceCatalog
from scripts.learning_bridge import LearningLedger

ROOT = Path(__file__).resolve().parents[1]
PROMO = "2026-10-28-shopify-expiring-offline-token-deadline-gate.json"
SOURCE_IDS = {"src_2bf95ae357249057", "src_42fcb436456bd9a0"}
LEARNING_ID = "learn_45023a81c7681335"


class ShopifyOfflineTokenPromotionTest(unittest.TestCase):
    def test_staged_learning_preserves_history_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge = root / "knowledge"
            promotions = knowledge / "promotions"
            promotions.mkdir(parents=True)
            for filename in ("source_catalog.json", "learning_ledger.json"):
                shutil.copy2(ROOT / "knowledge" / filename, knowledge / filename)
            shutil.copy2(ROOT / "knowledge" / "promotions" / PROMO, promotions / PROMO)

            source_path = knowledge / "source_catalog.json"
            learning_path = knowledge / "learning_ledger.json"
            before_sources = {x["source_id"] for x in json.loads(source_path.read_text())["sources"]}
            before_learnings = {x["learning_id"] for x in json.loads(learning_path.read_text())["learnings"]}

            first = apply_promotions(root)
            self.assertEqual(set(first["sources_created"]), SOURCE_IDS)
            self.assertEqual(first["learnings_created"], [LEARNING_ID])
            catalog = SourceCatalog(source_path)
            ledger = LearningLedger(learning_path, source_path)
            self.assertTrue(before_sources.issubset({x["source_id"] for x in catalog.list()}))
            self.assertTrue(before_learnings.issubset({x["learning_id"] for x in ledger.list()}))
            plan = {x["learning_id"]: x for x in ledger.for_plan("video_shopify")}
            self.assertIn(LEARNING_ID, plan)
            self.assertEqual(plan[LEARNING_ID]["status"], "active")
            self.assertTrue(all(catalog.find(s) is not None for s in plan[LEARNING_ID]["source_ids"]))
            self.assertNotIn(LEARNING_ID, {x["learning_id"] for x in ledger.for_plan("finance")})
            self.assertNotIn(LEARNING_ID, {x["learning_id"] for x in ledger.for_plan("system")})

            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
