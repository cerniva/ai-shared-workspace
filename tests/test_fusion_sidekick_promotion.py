"""Official Fusion/Sidekick promotion: identity, source lineage, idempotence, history."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import SourceCatalog, canonicalize, source_id
from scripts.learning_bridge import LearningLedger, learning_id
from scripts.knowledge_promote import apply_promotions

ROOT = Path(__file__).resolve().parents[1]
PROMO = "2026-10-29-fusion-sidekick-safety-gates.json"
SOURCE_IDS = {
    "src_af8e72e013cbe8cf",
    "src_c5b400f37c5fa56b",
    "src_6cdf73871e5749dd",
    "src_f4cfc2ae73bd073f",
}
LEARNING_IDS = {
    "learn_153d31716c7324ae",
    "learn_3108df4902c2b19e",
}


class FusionSidekickPromotionTests(unittest.TestCase):
    def test_schema_ids_gates_and_lineage(self):
        doc = json.loads((ROOT / "knowledge" / "promotions" / PROMO).read_text())
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual({s["source_id"] for s in doc["sources"]}, SOURCE_IDS)
        self.assertEqual({l["learning_id"] for l in doc["learnings"]}, LEARNING_IDS)
        self.assertEqual(len(set(doc["gates"])), 2)
        for src in doc["sources"]:
            self.assertEqual(src["source_id"], source_id(canonicalize(src["canonical"])))
            self.assertEqual(src["provenance"], "verified")
        for learning in doc["learnings"]:
            self.assertEqual(learning["learning_id"], learning_id(learning["domain"], learning["claim"]))
            self.assertTrue(set(learning["source_ids"]) <= SOURCE_IDS)
            self.assertEqual(learning["evidence_status"], "verified")
            self.assertEqual(learning["outcome"], "pending")
            self.assertIn("REVIEW_ONLY", learning["decision"])
            self.assertTrue(any(gate in learning["decision"] for gate in doc["gates"]))

    def test_additive_import_idempotence_and_plan_tags(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            knowledge = root / "knowledge"
            promos = knowledge / "promotions"
            promos.mkdir(parents=True)
            for name in ("source_catalog.json", "learning_ledger.json"):
                shutil.copy2(ROOT / "knowledge" / name, knowledge / name)
            shutil.copy2(ROOT / "knowledge" / "promotions" / PROMO, promos / PROMO)
            cp = knowledge / "source_catalog.json"
            lp = knowledge / "learning_ledger.json"
            before_sources = {x["source_id"]: x for x in json.loads(cp.read_text())["sources"]}
            before_learnings = {x["learning_id"]: x for x in json.loads(lp.read_text())["learnings"]}
            self.assertFalse(SOURCE_IDS & set(before_sources))
            self.assertFalse(LEARNING_IDS & set(before_learnings))
            first = apply_promotions(root)
            self.assertEqual(set(first["sources_created"]), SOURCE_IDS)
            self.assertEqual(set(first["learnings_created"]), LEARNING_IDS)
            catalog = SourceCatalog(cp)
            ledger = LearningLedger(lp, cp)
            self.assertTrue(all(before_sources[k] == next(s for s in catalog.list() if s["source_id"] == k) for k in before_sources))
            self.assertTrue(all(before_learnings[k] == next(l for l in ledger.list() if l["learning_id"] == k) for k in before_learnings))
            self.assertIn("learn_153d31716c7324ae", {l["learning_id"] for l in ledger.for_plan("system")})
            self.assertIn("learn_3108df4902c2b19e", {l["learning_id"] for l in ledger.for_plan("video_shopify")})
            second = apply_promotions(root)
            self.assertEqual(second["sources_created"], [])
            self.assertEqual(second["learnings_created"], [])
            self.assertEqual(second["changed_files"], [])


if __name__ == "__main__":
    unittest.main()
