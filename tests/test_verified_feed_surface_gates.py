"""Fail-closed regression for verified 2026-10-28 GitHub/Shopify feed gates.

Run only on a temporary copy of the canonical ledgers. Never modify main.
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
PROMO = "2026-10-28-verified-github-shopify-surface-gates.json"


class VerifiedFeedSurfaceGatesTest(unittest.TestCase):
    def test_additive_idempotent_and_plan_scoped(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            knowledge = root / "knowledge"
            promotions = knowledge / "promotions"
            promotions.mkdir(parents=True)
            for name in ("source_catalog.json", "learning_ledger.json"):
                shutil.copy2(ROOT / "knowledge" / name, knowledge / name)
            shutil.copy2(ROOT / "knowledge" / "promotions" / PROMO, promotions / PROMO)
            catalog_path = knowledge / "source_catalog.json"
            ledger_path = knowledge / "learning_ledger.json"
            before_sources = {x["source_id"] for x in json.loads(catalog_path.read_text())["sources"]}
            before_learnings = {x["learning_id"] for x in json.loads(ledger_path.read_text())["learnings"]}

            first = apply_promotions(root)
            self.assertEqual(set(first["sources_created"]), {
                "src_92608e65bdba9862", "src_0e76504be1989659"
            })
            self.assertEqual(set(first["learnings_created"]), {
                "learn_f179db9f3ae28d71", "learn_05ee8f4001db2a14"
            })
            catalog = SourceCatalog(catalog_path)
            ledger = LearningLedger(ledger_path, catalog_path)
            self.assertTrue(before_sources.issubset({x["source_id"] for x in catalog.list()}))
            self.assertTrue(before_learnings.issubset({x["learning_id"] for x in ledger.list()}))
            self.assertIn("learn_f179db9f3ae28d71", {
                x["learning_id"] for x in ledger.for_plan("system")
            })
            self.assertIn("learn_05ee8f4001db2a14", {
                x["learning_id"] for x in ledger.for_plan("video_shopify")
            })
            for item in ledger.list():
                if item["learning_id"] in {"learn_f179db9f3ae28d71", "learn_05ee8f4001db2a14"}:
                    self.assertTrue(item["source_ids"])
                    self.assertTrue(all(catalog.find(s) is not None for s in item["source_ids"]))

            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
