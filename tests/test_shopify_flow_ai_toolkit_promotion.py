"""Shopify Flow AI Toolkit staged learning: source-linked, additive, idempotent.

This test uses temporary catalog/ledger copies only and never calls Shopify.
"""
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import SourceCatalog
from scripts.learning_bridge import LearningLedger, learning_id
from scripts.knowledge_promote import apply_promotions

ROOT = Path(__file__).resolve().parents[1]
PROMO = "2026-10-28-shopify-flow-ai-toolkit-approval-gate.json"
SOURCE = "src_fa81d10c13f2496c"
LEARNING = "learn_e50637a7d14696cd"
GATE = "SHOPIFY_FLOW_AI_TOOLKIT_APPROVAL_GATE"


class ShopifyFlowAiToolkitPromotionTest(unittest.TestCase):
    def setUp(self):
        self.promotion = json.loads(
            (ROOT / "knowledge" / "promotions" / PROMO).read_text(encoding="utf-8")
        )

    def test_schema_ids_and_approval_gate(self):
        data = self.promotion
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["gates"], [GATE])
        source = data["sources"][0]
        self.assertEqual(source["source_id"], SOURCE)
        self.assertEqual(
            "src_" + hashlib.sha256(source["canonical"].encode("utf-8")).hexdigest()[:16],
            SOURCE,
        )
        self.assertEqual(source["provenance"], "verified")
        learning = data["learnings"][0]
        self.assertEqual(learning["learning_id"], LEARNING)
        self.assertEqual(learning_id(learning["domain"], learning["claim"]), LEARNING)
        self.assertEqual(learning["plan_tags"], ["video_shopify"])
        self.assertEqual(learning["source_ids"], [SOURCE])
        self.assertEqual(learning["status"], "active")
        self.assertIn("write_automations", learning["decision"])
        self.assertIn("read-only", learning["decision"])
        self.assertIn("third-party apps", learning["claim"])

    def test_additive_apply_twice(self):
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
            old_sources = {s["source_id"] for s in json.loads(source_path.read_text())["sources"]}
            old_learnings = {l["learning_id"] for l in json.loads(ledger_path.read_text())["learnings"]}
            first = apply_promotions(root)
            self.assertEqual(first["sources_created"], [SOURCE])
            self.assertEqual(first["learnings_created"], [LEARNING])
            catalog = SourceCatalog(source_path)
            ledger = LearningLedger(ledger_path, source_path)
            self.assertTrue(old_sources.issubset({s["source_id"] for s in catalog.list()}))
            self.assertTrue(old_learnings.issubset({l["learning_id"] for l in ledger.list()}))
            self.assertIn(LEARNING, {l["learning_id"] for l in ledger.for_plan("video_shopify")})
            self.assertNotIn(LEARNING, {l["learning_id"] for l in ledger.for_plan("finance")})
            self.assertNotIn(LEARNING, {l["learning_id"] for l in ledger.for_plan("system")})
            self.assertEqual(catalog.validate(), len(old_sources) + 1)
            self.assertEqual(ledger.validate(), len(old_learnings) + 1)
            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
