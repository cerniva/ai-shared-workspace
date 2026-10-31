"""Shopify UCP /buy discovery: deterministic, additive, privacy-safe review gate.

Tests use temporary ledgers; no Shopify account or checkout is accessed.
"""
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import SourceCatalog, canonicalize
from scripts.learning_bridge import LearningLedger, learning_id
from scripts.knowledge_promote import apply_promotions

ROOT = Path(__file__).resolve().parents[1]
PROMO = "2026-10-28-shopify-ucp-buy-link-discovery-gate.json"
SOURCE = "src_c35717da9d28cfb8"
LEARNING = "learn_2698c1ab36265386"
GATE = "SHOPIFY_UCP_BUY_LINK_DISCOVERY_GATE"


class ShopifyUcpBuyLinkPromotionTest(unittest.TestCase):
    def setUp(self):
        self.promotion = json.loads(
            (ROOT / "knowledge" / "promotions" / PROMO).read_text(encoding="utf-8")
        )

    def test_schema_stable_identity_source_and_privacy_gate(self):
        doc = self.promotion
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(doc["gates"], [GATE])
        self.assertEqual((len(doc["sources"]), len(doc["learnings"])), (1, 1))
        source = doc["sources"][0]
        learning = doc["learnings"][0]
        self.assertEqual(source["canonical"],
            "https://shopify.dev/changelog/posts/cart-and-checkout-permalinks-now-support-ucp-at-buy")
        self.assertEqual(source["source_id"], SOURCE)
        self.assertEqual("src_" + hashlib.sha256(
            canonicalize(source["canonical"]).encode("utf-8")).hexdigest()[:16], SOURCE)
        self.assertEqual(source["evidence_tier"], "official")
        self.assertEqual(source["access_status"], "verified-public")
        self.assertEqual(learning["learning_id"], LEARNING)
        self.assertEqual(learning_id(learning["domain"], learning["claim"]), LEARNING)
        self.assertEqual(learning["source_ids"], [SOURCE])
        self.assertEqual(learning["plan_tags"], ["video_shopify"])
        self.assertEqual(learning["status"], "active")
        self.assertIn(GATE, learning["decision"])
        for required in ("/.well-known/ucp", "config.endpoint", "/cart", "Shorts",
                         "buyer personal details", "REVIEW_ONLY", "N/A", "applied_learning_ids"):
            self.assertIn(required, learning["decision"])
        self.assertIn("does not establish", learning["claim"])

    def test_additive_idempotent_import_and_plan_filter(self):
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
            original_sources = json.loads(source_path.read_text(encoding="utf-8"))["sources"]
            original_learnings = json.loads(ledger_path.read_text(encoding="utf-8"))["learnings"]
            first = apply_promotions(root)
            self.assertEqual(first["sources_created"], [SOURCE])
            self.assertEqual(first["learnings_created"], [LEARNING])
            catalog = SourceCatalog(source_path)
            ledger = LearningLedger(ledger_path, source_path)
            saved_sources = {s["source_id"]: s for s in catalog.list()}
            saved_learnings = {l["learning_id"]: l for l in ledger.list()}
            for row in original_sources:
                self.assertEqual(saved_sources[row["source_id"]], row)
            for row in original_learnings:
                self.assertEqual(saved_learnings[row["learning_id"]], row)
            self.assertIn(LEARNING, {l["learning_id"] for l in ledger.for_plan("video_shopify")})
            self.assertNotIn(LEARNING, {l["learning_id"] for l in ledger.for_plan("finance")})
            self.assertNotIn(LEARNING, {l["learning_id"] for l in ledger.for_plan("system")})
            self.assertEqual(catalog.validate(), len(original_sources) + 1)
            self.assertEqual(ledger.validate(), len(original_learnings) + 1)
            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
