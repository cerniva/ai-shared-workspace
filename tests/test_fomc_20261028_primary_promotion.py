"""Fail-closed, additive promotion regression for the 2026-10-28 FOMC statement.

Tests only temporary copies of the source catalog and learning ledger.
Does not assert that a real Finance production report has consumed the learning.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import SourceCatalog
from scripts.knowledge_promote import apply_promotions
from scripts.learning_bridge import LearningLedger

ROOT = Path(__file__).resolve().parents[1]
PROMO = "2026-10-28-fed-fomc-hold-primary-gate.json"
SOURCE_ID = "src_a0c3e1be77e8b5a2"
LEARNING_ID = "learn_acfe0f34f57aa6cb"
OLD_LEARNING_ID = "learn_9b39644affcb8a33"


class FomcOctoberPrimaryPromotionTest(unittest.TestCase):
    def test_schema_and_freshness_gate(self):
        data = json.loads((ROOT / "knowledge" / "promotions" / PROMO).read_text())
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["gates"], ["FED_FOMC_20261028_CURRENT_PRIMARY_GATE"])
        self.assertEqual(data["sources"][0]["source_id"], SOURCE_ID)
        self.assertEqual(data["learnings"][0]["source_ids"], [SOURCE_ID])
        self.assertEqual(data["learnings"][0]["plan_tags"], ["finance"])
        self.assertEqual(data["learnings"][0]["status"], "active")
        decision = data["learnings"][0]["decision"]
        self.assertIn("October 28", decision)
        self.assertIn("September 16", decision)
        self.assertIn("applied_learning_ids", decision)

    def test_additive_idempotent_and_historical_learning_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            knowledge = root / "knowledge"
            promotions = knowledge / "promotions"
            promotions.mkdir(parents=True)
            for name in ("source_catalog.json", "learning_ledger.json"):
                shutil.copy2(ROOT / "knowledge" / name, knowledge / name)
            shutil.copy2(ROOT / "knowledge" / "promotions" / PROMO, promotions / PROMO)
            catalog_path = knowledge / "source_catalog.json"
            ledger_path = knowledge / "learning_ledger.json"
            old_sources = {x["source_id"] for x in json.loads(catalog_path.read_text())["sources"]}
            old_learnings = {x["learning_id"] for x in json.loads(ledger_path.read_text())["learnings"]}
            self.assertIn(OLD_LEARNING_ID, old_learnings)
            self.assertNotIn(SOURCE_ID, old_sources)
            self.assertNotIn(LEARNING_ID, old_learnings)

            first = apply_promotions(root)
            self.assertEqual(first["sources_created"], [SOURCE_ID])
            self.assertEqual(first["learnings_created"], [LEARNING_ID])
            catalog = SourceCatalog(catalog_path)
            ledger = LearningLedger(ledger_path, catalog_path)
            self.assertTrue(old_sources.issubset({x["source_id"] for x in catalog.list()}))
            self.assertTrue(old_learnings.issubset({x["learning_id"] for x in ledger.list()}))
            self.assertIn(OLD_LEARNING_ID, {x["learning_id"] for x in ledger.list()})
            self.assertIn(LEARNING_ID, {x["learning_id"] for x in ledger.for_plan("finance")})
            self.assertIsNotNone(catalog.find(SOURCE_ID))
            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
