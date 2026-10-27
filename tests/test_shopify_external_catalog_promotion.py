"""Offline regression gates for the verified Shopify Catalog external beta promotion.

No network, store mutation, catalog rewrite, or PayoutLens access.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, canonicalize, normalize_record, source_id
from scripts.learning_bridge import learning_id, normalize_learning

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

    def test_runtime_validators_reject_corrupt_promotion(self) -> None:
        src, learn = self.doc["source"], self.doc["learning"]
        self.assertEqual(normalize_record(src)["source_id"], src["source_id"])
        self.assertEqual(
            normalize_learning(learn, {src["source_id"]})["learning_id"],
            learn["learning_id"],
        )
        with self.assertRaises(CatalogError):
            normalize_record({**src, "canonical": "https://user:pass@shopify.dev/unsafe"})
        with self.assertRaises(CatalogError):
            normalize_learning({**learn, "source_ids": ["src_missing"]}, {src["source_id"]})
        with self.assertRaises(CatalogError):
            normalize_learning({**learn, "plan_tags": ["unknown_plan"]}, {src["source_id"]})

    def test_no_duplicate_staged_source_learning_or_gate(self) -> None:
        src, learn = self.doc["source"], self.doc["learning"]
        canonical = canonicalize(src["canonical"])
        for path in (ROOT / "knowledge/promotions").glob("*.json"):
            if path == PROMOTION:
                continue
            other = json.loads(path.read_text(encoding="utf-8"))
            rows = list(other.get("sources") or [])
            if isinstance(other.get("source"), dict):
                rows.append(other["source"])
            for row in rows:
                if not isinstance(row, dict):
                    continue
                self.assertNotEqual(row.get("source_id"), src["source_id"], str(path))
                if row.get("canonical"):
                    self.assertNotEqual(canonicalize(row["canonical"]), canonical, str(path))
            learnings = list(other.get("learnings") or [])
            if isinstance(other.get("learning"), dict):
                learnings.append(other["learning"])
            for row in learnings:
                if isinstance(row, dict):
                    self.assertNotEqual(row.get("learning_id"), learn["learning_id"], str(path))
            self.assertNotIn(GATE, other.get("gates") or [], str(path))

    def test_fail_closed_external_product_rules(self) -> None:
        claim = self.doc["learning"]["claim"]
        decision = self.doc["learning"]["decision"]
        self.assertIn("eligible.native_checkout=false", claim)
        self.assertIn("only for US shoppers", claim)
        self.assertIn("do not earn Promoted Placements commission", claim)
        self.assertIn("REVIEW_ONLY", decision)
        self.assertIn("applied_learning_ids", self.doc["learning"]["next_measurement"])
        self.assertIn("no changes", decision)


class ShopifyExternalOfferRightsPromotionTests(unittest.TestCase):
    """The separate official extension doc adds display and data-use rules."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.doc = json.loads(
            (ROOT / "knowledge/promotions/2026-10-28-shopify-external-offer-display-rights.json")
            .read_text(encoding="utf-8")
        )
        cls.beta = json.loads(PROMOTION.read_text(encoding="utf-8"))
        cls.catalog = json.loads((ROOT / "knowledge/source_catalog.json").read_text(encoding="utf-8"))
        cls.ledger = json.loads((ROOT / "knowledge/learning_ledger.json").read_text(encoding="utf-8"))

    def test_schema_identity_and_runtime_validation(self) -> None:
        src, learn = self.doc["source"], self.doc["learning"]
        self.assertEqual(self.doc["schema_version"], 1)
        self.assertEqual(self.doc["gates"], ["SHOPIFY_EXTERNAL_OFFER_DISPLAY_RIGHTS_GATE"])
        self.assertEqual(src["source_id"], source_id(canonicalize(src["canonical"])))
        self.assertEqual(learn["learning_id"], learning_id(learn["domain"], learn["claim"]))
        self.assertEqual(learn["source_ids"], [src["source_id"]])
        self.assertEqual(learn["plan_tags"], ["video_shopify"])
        self.assertEqual(learn["status"], "active")
        self.assertEqual(learn["evidence_status"], "verified")
        self.assertEqual(normalize_record(src)["source_id"], src["source_id"])
        self.assertEqual(
            normalize_learning(learn, {src["source_id"]})["learning_id"],
            learn["learning_id"],
        )

    def test_additive_no_duplicate_with_main_or_beta(self) -> None:
        src, learn = self.doc["source"], self.doc["learning"]
        beta_src, beta_learn = self.beta["source"], self.beta["learning"]
        self.assertNotEqual(src["source_id"], beta_src["source_id"])
        self.assertNotEqual(canonicalize(src["canonical"]), canonicalize(beta_src["canonical"]))
        self.assertNotEqual(learn["learning_id"], beta_learn["learning_id"])
        self.assertTrue(set(self.doc["gates"]).isdisjoint(self.beta["gates"]))
        self.assertNotIn(src["source_id"], {s["source_id"] for s in self.catalog["sources"]})
        self.assertNotIn(
            canonicalize(src["canonical"]),
            {canonicalize(s["canonical"]) for s in self.catalog["sources"]},
        )
        self.assertNotIn(learn["learning_id"], {l["learning_id"] for l in self.ledger["learnings"]})

    def test_rights_price_and_access_gates_are_explicit(self) -> None:
        claim = self.doc["learning"]["claim"]
        decision = self.doc["learning"]["decision"]
        for phrase in (
            "seller.name", "variants[].url", "may not be rehosted",
            "train/evaluate machine-learning models", "current shopper session",
            "availability.available=true", "2026-08-25", "enabled client",
        ):
            self.assertIn(phrase, claim)
        self.assertIn("REVIEW_ONLY", decision)
        self.assertIn("applied_learning_ids", self.doc["learning"]["next_measurement"])
        self.assertIn("No live store or content publication", decision)


if __name__ == "__main__":
    unittest.main()
