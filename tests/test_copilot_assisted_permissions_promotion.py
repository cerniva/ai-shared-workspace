"""Offline validation for the Copilot assisted-permissions review-only promotion.

Does not change repository permissions, invoke Copilot, or modify history.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, canonicalize, normalize_record, source_id
from scripts.learning_bridge import learning_id, normalize_learning

ROOT = Path(__file__).resolve().parents[1]
PROMOTION = ROOT / "knowledge/promotions/2026-10-28-github-copilot-assisted-permissions-review-gate.json"
GATE = "COPILOT_ASSISTED_PERMISSIONS_REVIEW_GATE"


class CopilotAssistedPermissionsPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(PROMOTION.read_text(encoding="utf-8"))
        cls.catalog = json.loads((ROOT / "knowledge/source_catalog.json").read_text(encoding="utf-8"))
        cls.ledger = json.loads((ROOT / "knowledge/learning_ledger.json").read_text(encoding="utf-8"))

    def test_schema_identity_reference_and_runtime_validation(self):
        doc = self.doc
        source, learning = doc["source"], doc["learning"]
        self.assertEqual(doc["schema_version"], 1)
        self.assertEqual(doc["gates"], [GATE])
        self.assertEqual(source["source_id"], source_id(canonicalize(source["canonical"])))
        self.assertEqual(learning["learning_id"], learning_id(learning["domain"], learning["claim"]))
        self.assertEqual(learning["source_ids"], [source["source_id"]])
        self.assertEqual(learning["plan_tags"], ["system"])
        self.assertEqual(learning["status"], "active")
        self.assertEqual(learning["evidence_status"], "verified")
        self.assertIn(GATE, learning["decision"])
        self.assertEqual(normalize_record(source)["source_id"], source["source_id"])
        self.assertEqual(normalize_learning(learning, {source["source_id"]})["learning_id"], learning["learning_id"])

    def test_additive_no_duplicate_identity_or_canonical(self):
        source, learning = self.doc["source"], self.doc["learning"]
        canonical = canonicalize(source["canonical"])
        for old in self.catalog["sources"]:
            if old["source_id"] == source["source_id"]:
                self.assertEqual(canonicalize(old["canonical"]), canonical)
            if canonicalize(old["canonical"]) == canonical:
                self.assertEqual(old["source_id"], source["source_id"])
        for old in self.ledger["learnings"]:
            if old["learning_id"] == learning["learning_id"]:
                self.assertEqual((old["domain"], old["claim"]), (learning["domain"], learning["claim"]))
        for path in (ROOT / "knowledge/promotions").glob("*.json"):
            if path == PROMOTION:
                continue
            doc = json.loads(path.read_text(encoding="utf-8"))
            sources = list(doc.get("sources") or [])
            if isinstance(doc.get("source"), dict):
                sources.append(doc["source"])
            for old in sources:
                if isinstance(old, dict) and old.get("canonical"):
                    self.assertNotEqual(canonicalize(old["canonical"]), canonical, str(path))
            learnings = list(doc.get("learnings") or [])
            if isinstance(doc.get("learning"), dict):
                learnings.append(doc["learning"])
            for old in learnings:
                if isinstance(old, dict):
                    self.assertNotEqual(old.get("learning_id"), learning["learning_id"], str(path))
            self.assertNotIn(GATE, doc.get("gates") or [], str(path))

    def test_fail_closed_permissions_scope_and_corrupt_records(self):
        source, learning = self.doc["source"], self.doc["learning"]
        self.assertIn("other requests still require user approval", learning["claim"])
        self.assertIn("does not grant permissions to unrelated GitHub connectors", learning["claim"])
        self.assertIn("Do not claim this changes GitHub connector permissions", learning["decision"])
        self.assertIn("applied_learning_ids", learning["next_measurement"])
        with self.assertRaises(CatalogError):
            normalize_record({**source, "canonical": "https://user:pass@github.blog/unsafe"})
        with self.assertRaises(CatalogError):
            normalize_learning({**learning, "source_ids": ["src_missing"]}, {source["source_id"]})
        with self.assertRaises(CatalogError):
            normalize_learning({**learning, "plan_tags": ["unknown_plan"]}, {source["source_id"]})


if __name__ == "__main__":
    unittest.main()
