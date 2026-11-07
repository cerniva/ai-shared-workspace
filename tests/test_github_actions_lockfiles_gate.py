"""Regression for 2026-10-28 GitHub Actions lockfile GA promotion.

Runs only on temporary copies of the shared catalog/ledger; never edits main.
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
PROMO = "2026-10-29-github-actions-lockfiles-ga.json"
SOURCE_IDS = {"src_ad19e1712c42ab02", "src_76811b880217b4a5"}
LEARNING_ID = "learn_87c7a637c2654b3f"


class ActionsLockfilesGATest(unittest.TestCase):
    def test_additive_idempotent_plan_scoped_and_source_linked(self):
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
            old_sources = json.loads(catalog_path.read_text())["sources"]
            old_learnings = json.loads(ledger_path.read_text())["learnings"]
            staged = json.loads((promotions / PROMO).read_text())
            self.assertEqual(staged["schema_version"], 1)
            self.assertEqual(staged["gates"], ["ACTIONS_LOCKFILE_ADOPTION_GATE"])
            self.assertEqual({s["source_id"] for s in staged["sources"]}, SOURCE_IDS)
            self.assertEqual(staged["learnings"][0]["learning_id"], LEARNING_ID)
            self.assertTrue(set(staged["learnings"][0]["source_ids"]) <= SOURCE_IDS)

            first = apply_promotions(root)
            self.assertEqual(set(first["sources_created"]), SOURCE_IDS)
            self.assertEqual(first["learnings_created"], [LEARNING_ID])
            catalog = SourceCatalog(catalog_path)
            ledger = LearningLedger(ledger_path, catalog_path)
            saved_sources = {s["source_id"]: s for s in catalog.list()}
            saved_learnings = {l["learning_id"]: l for l in ledger.list()}
            for row in old_sources:
                self.assertEqual(saved_sources[row["source_id"]], row)
            for row in old_learnings:
                self.assertEqual(saved_learnings[row["learning_id"]], row)
            self.assertTrue(SOURCE_IDS <= saved_sources.keys())
            self.assertIn(LEARNING_ID, saved_learnings)
            self.assertEqual(set(saved_learnings[LEARNING_ID]["source_ids"]), SOURCE_IDS)
            self.assertIn(LEARNING_ID, {l["learning_id"] for l in ledger.for_plan("system")})
            self.assertNotIn(LEARNING_ID, {l["learning_id"] for l in ledger.for_plan("finance")})
            self.assertNotIn(LEARNING_ID, {l["learning_id"] for l in ledger.for_plan("video_shopify")})

            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
