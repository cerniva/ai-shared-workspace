"""ShopifyQL parseWarnings 2026-10 staged promotion: additive, safe, idempotent.

Runs only against temporary catalog/ledger copies. Does not call Shopify APIs.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import SourceCatalog
from scripts.learning_bridge import LearningLedger
from scripts.knowledge_promote import apply_promotions

ROOT = Path(__file__).resolve().parents[1]
PROMO = "2026-10-28-shopifyql-parsewarnings-compatibility-gate.json"
SOURCES = {"src_3a3b7df8e3c94ed6", "src_b03e0bdfdd181c26"}
LEARNING = "learn_407955adc6c87efb"
GATE = "SHOPIFYQL_PARSE_WARNINGS_VERSION_GATE"


class ShopifyqlParseWarningsPromotionTest(unittest.TestCase):
    def setUp(self):
        self.promotion = json.loads((ROOT / "knowledge" / "promotions" / PROMO).read_text(encoding="utf-8"))

    def test_schema_and_version_gate(self):
        self.assertEqual(self.promotion["schema_version"], 1)
        self.assertEqual(self.promotion["gates"], [GATE])
        self.assertEqual({x["source_id"] for x in self.promotion["sources"]}, SOURCES)
        learning = self.promotion["learnings"][0]
        self.assertEqual(learning["learning_id"], LEARNING)
        self.assertEqual(learning["plan_tags"], ["video_shopify"])
        self.assertEqual(learning["status"], "active")
        self.assertEqual(set(learning["source_ids"]), SOURCES)
        self.assertIn("2026-10", learning["decision"])
        self.assertIn("older API versions", learning["decision"])

    def test_additive_apply_and_second_run_noop(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            knowledge = root / "knowledge"
            promos = knowledge / "promotions"
            promos.mkdir(parents=True)
            for filename in ("source_catalog.json", "learning_ledger.json"):
                shutil.copy2(ROOT / "knowledge" / filename, knowledge / filename)
            shutil.copy2(ROOT / "knowledge" / "promotions" / PROMO, promos / PROMO)
            source_path = knowledge / "source_catalog.json"
            ledger_path = knowledge / "learning_ledger.json"
            old_sources = {x["source_id"] for x in json.loads(source_path.read_text())["sources"]}
            old_learnings = {x["learning_id"] for x in json.loads(ledger_path.read_text())["learnings"]}
            first = apply_promotions(root)
            self.assertEqual(set(first["sources_created"]), SOURCES)
            self.assertEqual(first["learnings_created"], [LEARNING])
            catalog = SourceCatalog(source_path)
            ledger = LearningLedger(ledger_path, source_path)
            self.assertTrue(old_sources.issubset({x["source_id"] for x in catalog.list()}))
            self.assertTrue(old_learnings.issubset({x["learning_id"] for x in ledger.list()}))
            self.assertIn(LEARNING, {x["learning_id"] for x in ledger.for_plan("video_shopify")})
            self.assertNotIn(LEARNING, {x["learning_id"] for x in ledger.for_plan("finance")})
            self.assertNotIn(LEARNING, {x["learning_id"] for x in ledger.for_plan("system")})
            catalog.validate()
            ledger.validate()
            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
