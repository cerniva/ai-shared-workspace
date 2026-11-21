"""Promotion contract for official Shopify App Events Analytics evidence (review-only)."""
import json
import unittest
from pathlib import Path

from scripts.knowledge_bridge import canonicalize, source_id
from scripts.learning_bridge import learning_id


ROOT = Path(__file__).resolve().parents[1]
PROMOTION = ROOT / "knowledge/promotions/2026-10-30-shopify-app-events-analytics-declaration-gate.json"
GATE = "SHOPIFY_APP_EVENTS_ANALYTICS_DECLARATION_RETENTION_GATE"


class ShopifyAppEventsAnalyticsPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(PROMOTION.read_text(encoding="utf-8"))

    def test_schema_and_deterministic_ids(self):
        doc = self.doc
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(doc["gates"], [GATE])
        self.assertEqual(len(doc["sources"]), 2)
        self.assertEqual(len(doc["learnings"]), 1)
        for source in doc["sources"]:
            self.assertEqual(source["source_id"], source_id(canonicalize(source["canonical"])))
            self.assertEqual(source["evidence_tier"], "official")
            self.assertEqual(source["access_status"], "verified-public")
        learning = doc["learnings"][0]
        self.assertEqual(learning["learning_id"], learning_id(learning["domain"], learning["claim"]))
        self.assertEqual(set(learning["source_ids"]), {s["source_id"] for s in doc["sources"]})
        self.assertEqual(learning["plan_tags"], ["video_shopify"])
        self.assertEqual(learning["status"], "active")

    def test_receipt_is_not_analytics_proof(self):
        learning = self.doc["learnings"][0]
        self.assertIn("202 Accepted", learning["claim"])
        self.assertIn("does not prove analytics availability", learning["claim"])
        self.assertIn("released analytics_app_events declaration", learning["claim"])
        self.assertIn("REVIEW_ONLY", learning["decision"])
        self.assertIn("actual report artifact", learning["decision"])

    def test_retention_privacy_and_authorization_gates(self):
        learning = self.doc["learnings"][0]
        for expected in ("30 days", "365 days", "identifying personal data", "other datasets"):
            self.assertIn(expected, learning["claim"])
        for expected in ("authorized installed Shopify app", "30-day", "365-day",
                         "no cross-dataset query", "Do not deploy"):
            self.assertIn(expected, learning["decision"])
        self.assertEqual(learning["outcome"], "pending")


if __name__ == "__main__":
    unittest.main()
