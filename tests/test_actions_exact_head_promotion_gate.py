"""Regression for GitHub Actions exact-head CI evidence promotion (PR #376)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.knowledge_bridge import canonicalize, source_id
from scripts.learning_bridge import learning_id
from scripts import takipci_denetci as auditor

ROOT = Path(__file__).resolve().parents[1]
PROMOTION = ROOT / "knowledge/promotions/2026-10-29-actions-exact-head-run-filter.json"


class ActionsExactHeadPromotionGateTests(unittest.TestCase):
    def test_schema_identity_dedup_and_source_lineage(self):
        doc = json.loads(PROMOTION.read_text(encoding="utf-8"))
        catalog = json.loads((ROOT / "knowledge/source_catalog.json").read_text(encoding="utf-8"))
        ledger = json.loads((ROOT / "knowledge/learning_ledger.json").read_text(encoding="utf-8"))
        source, learning = doc["source"], doc["learning"]
        canonical = canonicalize(source["canonical"])
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(canonical, "https://docs.github.com/en/rest/actions/workflow-runs")
        self.assertEqual(source["source_id"], source_id(canonical))
        self.assertEqual(learning["learning_id"], learning_id(learning["domain"], learning["claim"]))
        self.assertEqual(learning["source_ids"], [source["source_id"]])
        self.assertEqual(learning["plan_tags"], ["system"])
        self.assertEqual(learning["status"], "active")
        self.assertEqual(doc["gates"], ["ACTIONS_EXACT_HEAD_RUN_SCOPE_GATE"])
        self.assertFalse(any(canonicalize(row["canonical"]) == canonical for row in catalog["sources"]))
        self.assertFalse(any(row["learning_id"] == learning["learning_id"] for row in ledger["learnings"]))

    def test_foreign_head_failure_cannot_mask_current_head_failure(self):
        head = "exact-current-head"
        repo = "cerniva/ai-shared-workspace"
        refs = [
            {"id": 101, "ref_repo": None, "run": {
                "id": 101, "status": "completed", "conclusion": "failure",
                "head_sha": "historical-other-head", "repository": {"full_name": repo}}},
            {"id": 102, "ref_repo": None, "run": {
                "id": 102, "status": "completed", "conclusion": "failure",
                "head_sha": head, "repository": {"full_name": repo}}},
        ]
        reasons, warnings = auditor.check_run_refs(refs, repo, head)
        self.assertTrue(any("102" in reason for reason in reasons))
        self.assertFalse(any("101" in reason for reason in reasons))
        self.assertTrue(any("101" in warning and "historical" in warning for warning in warnings))


if __name__ == "__main__":
    unittest.main()
