"""Regression for additive Shopify Product Insights app-surface correction."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.learning_bridge import LearningLedger, persistence_gate


ROOT = Path(__file__).resolve().parents[1]
PROMOTION = ROOT / "knowledge/promotions/2026-10-28-shopify-product-insights-app-surface.json"
OLD_ID = "learn_f0de38014bef7448"
SOURCE_ID = "src_97a7eb010a0d1efa"
GATE = "PRODUCT_INSIGHTS_APP_SURFACE_GATE"


class ShopifyProductInsightsAppSurfaceTests(unittest.TestCase):
    def test_promotion_additive_and_plan_visible(self):
        promotion = json.loads(PROMOTION.read_text(encoding="utf-8"))
        self.assertEqual(promotion["schema_version"], 1)
        self.assertEqual(promotion["gates"], [GATE])
        self.assertEqual(len(promotion["learnings"]), 1)
        learning = promotion["learnings"][0]
        self.assertEqual(learning["source_ids"], [SOURCE_ID])
        self.assertEqual(learning["supersedes"], OLD_ID)
        self.assertEqual(learning["plan_tags"], ["video_shopify"])
        self.assertIn(GATE, learning["decision"])

        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            catalog = temp / "source_catalog.json"
            ledger_path = temp / "learning_ledger.json"
            catalog.write_bytes((ROOT / "knowledge/source_catalog.json").read_bytes())
            ledger_path.write_bytes((ROOT / "knowledge/learning_ledger.json").read_bytes())
            ledger = LearningLedger(ledger_path, catalog)
            original_ids = {row["learning_id"] for row in ledger.list()}
            self.assertIn(OLD_ID, original_ids)
            self.assertIn(SOURCE_ID, {row["source_id"] for row in json.loads(catalog.read_text())["sources"]})

            saved, created = ledger.add(learning)
            self.assertTrue(created)
            self.assertEqual(saved["supersedes"], OLD_ID)
            self.assertEqual(ledger.validate(), len(original_ids) + 1)
            after_ids = {row["learning_id"] for row in ledger.list()}
            self.assertTrue(original_ids.issubset(after_ids))
            active = {row["learning_id"] for row in ledger.for_plan("video_shopify")}
            self.assertIn(saved["learning_id"], active)
            self.assertNotIn(OLD_ID, active)
            self.assertTrue(persistence_gate(ledger, GATE)["persisted"])


if __name__ == "__main__":
    unittest.main()
