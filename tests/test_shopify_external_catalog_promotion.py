"""Offline regression gates for the verified Shopify Catalog external beta promotion.

No network, store mutation, catalog rewrite, or PayoutLens access.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.knowledge_bridge import canonicalize, source_id
from scripts.learning_bridge import learning_id

ROOT = Path(__file__).resolve().parents[1]
PROMOTION = ROOT / "knowledge/promotions/2026-10-28-shopify-external-catalog-beta-gate.json"
GATE = "SHOPIFY_CATALOG_EXTERNAL_US_ONLY_NO_CHECKOUT_GATE"


class ShopifyExternalCatalogPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(PROMOTION.read_text(encoding="utf-8"))
        cls.catalog = json.loads((ROOT / "knowledge/source_catalog.json").read_text(encoding="utf-8"))
        cls.ledger = json.loads((ROOT / "knowledge/learning_ledger.json").read_text(encoding="utf-8"))

    def test_schema_ids_and_source_reference(self) -> None:
        d = self.doc
        self.assertEqual(d["schema_version"], 1)
        self.assertEqual(d["gates"], [GATE])
        src, learn = d["source"], d["learning"]
        self.assertEqual(src["source_id"], source_id(canonicalize(src["canonical"])))
        self.assertEqual(learn["learning_id"], learning_id(learn["domain"], learn["claim"]))
        self.assertEqual(learn["source_ids"], [src["source_id"]])
        self.assertEqual(learn["plan_tags"], ["video_shopify"])
        self.assertEqual(learn["status"], "active")
        self.assertEqual(learn["evidence_status"], "verified")
        self.assertIn(GATE, learn["decision"])

    def test_no_conflicting_existing_identity(self) -> None:
        src, learn = self.doc["source"], self.doc["learning"]
        for old in self.catalog["sources"]:
            if old["source_id"] == src["source_id"]:
                self.assertEqual(canonicalize(old["canonical"]), canonicalize(src["canonical"]))
            if canonicalize(old["canonical"]) == canonicalize(src["canonical"]):
                self.assertEqual(old["source_id"], src["source_id"])
        for old in self.ledger["learnings"]:
            if old["learning_id"] == learn["learning_id"]:
                self.assertEqual(old["domain"], learn["domain"])
                self.assertEqual(old["claim"], learn["claim"])
                self.assertEqual(set(old["source_ids"]), set(learn["source_ids"]))

    def test_fail_closed_external_product_rules(self) -> None:
        claim = self.doc["learning"]["claim"]
        decision = self.doc["learning"]["decision"]
        self.assertIn("eligible.native_checkout=false", claim)
        self.assertIn("only for US shoppers", claim)
        self.assertIn("do not earn Promoted Placements commission", claim)
        self.assertIn("REVIEW_ONLY", decision)
        self.assertIn("applied_learning_ids", self.doc["learning"]["next_measurement"])
        self.assertIn("no changes", decision)


if __name__ == "__main__":
    unittest.main()
