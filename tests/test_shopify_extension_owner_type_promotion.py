"""Shopify API 2027-01 owner_type staged promotion; never changes canonical ledgers."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import SourceCatalog
from scripts.learning_bridge import LearningLedger
from scripts.knowledge_promote import apply_promotions

ROOT = Path(__file__).resolve().parents[1]
PROMO = "2026-10-28-shopify-extension-owner-type-2027-01-gate.json"
SOURCE = "src_ed378d3aeb2a17f9"
LEARNING = "learn_a581f048146641f8"
GATE = "SHOPIFY_EXTENSION_OWNER_TYPE_2027_01_GATE"


class ShopifyExtensionOwnerTypePromotionTest(unittest.TestCase):
    def setUp(self):
        self.promotion = json.loads((ROOT / "knowledge" / "promotions" / PROMO).read_text(encoding="utf-8"))

    def test_schema_ids_and_conditional_gate(self):
        p = self.promotion
        self.assertEqual(p["schema_version"], 1)
        self.assertEqual(p["gates"], [GATE])
        self.assertEqual([x["source_id"] for x in p["sources"]], [SOURCE])
        self.assertEqual([x["learning_id"] for x in p["learnings"]], [LEARNING])
        learning = p["learnings"][0]
        self.assertEqual(learning["source_ids"], [SOURCE])
        self.assertEqual(learning["plan_tags"], ["video_shopify"])
        self.assertEqual(learning["status"], "active")
        self.assertIn("2027-01", learning["decision"])
        self.assertIn("N/A", learning["decision"])
        self.assertIn("shopify.extension.toml", learning["next_measurement"])

    def test_additive_idempotent_and_plan_scoped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            knowledge = root / "knowledge"
            promos = knowledge / "promotions"
            promos.mkdir(parents=True)
            for name in ("source_catalog.json", "learning_ledger.json"):
                shutil.copy2(ROOT / "knowledge" / name, knowledge / name)
            shutil.copy2(ROOT / "knowledge" / "promotions" / PROMO, promos / PROMO)
            source_path = knowledge / "source_catalog.json"
            ledger_path = knowledge / "learning_ledger.json"
            old_sources = {x["source_id"] for x in json.loads(source_path.read_text())["sources"]}
            old_learnings = {x["learning_id"] for x in json.loads(ledger_path.read_text())["learnings"]}
            first = apply_promotions(root)
            self.assertEqual(first["sources_created"], [SOURCE])
            self.assertEqual(first["learnings_created"], [LEARNING])
            sources = SourceCatalog(source_path)
            learnings = LearningLedger(ledger_path, source_path)
            self.assertTrue(old_sources.issubset({x["source_id"] for x in sources.list()}))
            self.assertTrue(old_learnings.issubset({x["learning_id"] for x in learnings.list()}))
            self.assertIn(LEARNING, {x["learning_id"] for x in learnings.for_plan("video_shopify")})
            for plan in ("finance", "system"):
                self.assertNotIn(LEARNING, {x["learning_id"] for x in learnings.for_plan(plan)})
            sources.validate()
            learnings.validate()
            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
