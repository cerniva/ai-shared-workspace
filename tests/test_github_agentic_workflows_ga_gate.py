"""Regression: additive, idempotent GitHub Agentic Workflows GA trust gate.

Runs promotion against temporary catalog/ledger copies only; no main mutations.
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
PROMO = "2026-10-29-github-agentic-workflows-ga-trust-gate.json"
SOURCE_IDS = {"src_4dba21c9e50a763f", "src_a84e3c76f0b91d25"}
LEARNING_ID = "learn_2e94d16ab730c85f"
GATE = "AGENTIC_WORKFLOWS_TRUST_BUDGET_GATE"


class AgenticWorkflowsGATest(unittest.TestCase):
    def test_review_only_additive_source_linked_and_idempotent(self):
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
            before_sources = json.loads(catalog_path.read_text())["sources"]
            before_learnings = json.loads(ledger_path.read_text())["learnings"]
            staged = json.loads((promotions / PROMO).read_text())
            self.assertEqual(staged["schema_version"], 1)
            self.assertEqual(staged["gates"], [GATE])
            self.assertEqual({s["source_id"] for s in staged["sources"]}, SOURCE_IDS)
            self.assertEqual([x["learning_id"] for x in staged["learnings"]], [LEARNING_ID])
            self.assertEqual(set(staged["learnings"][0]["source_ids"]), SOURCE_IDS)
            self.assertIn("REVIEW_ONLY", staged["learnings"][0]["decision"])

            first = apply_promotions(root)
            self.assertEqual(set(first["sources_created"]), SOURCE_IDS)
            self.assertEqual(first["learnings_created"], [LEARNING_ID])
            saved_sources = {x["source_id"]: x for x in SourceCatalog(catalog_path).list()}
            ledger = LearningLedger(ledger_path, catalog_path)
            saved_learnings = {x["learning_id"]: x for x in ledger.list()}
            for row in before_sources:
                self.assertEqual(saved_sources[row["source_id"]], row)
            for row in before_learnings:
                self.assertEqual(saved_learnings[row["learning_id"]], row)
            self.assertEqual(set(saved_learnings[LEARNING_ID]["source_ids"]), SOURCE_IDS)
            self.assertIn(LEARNING_ID, {x["learning_id"] for x in ledger.for_plan("system")})
            for other in ("finance", "video_shopify"):
                self.assertNotIn(LEARNING_ID, {x["learning_id"] for x in ledger.for_plan(other)})

            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
