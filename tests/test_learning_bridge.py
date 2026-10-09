from __future__ import annotations

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, SourceCatalog
from scripts.learning_bridge import LearningLedger, learning_id, persistence_gate


class LearningBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.catalog_path = root / "source_catalog.json"
        self.ledger_path = root / "learning_ledger.json"
        source, _ = SourceCatalog(self.catalog_path).add(
            {
                "source_name": "Official docs",
                "canonical": "https://example.com/docs",
                "category": "test",
                "purpose": "Test source",
                "evidence_tier": "official",
                "access_status": "verified-public",
                "cost_quota": "free",
                "reliability_limits": "Fixture only",
                "discovered_at": "2026-09-28T01:59:00+00:00",
                "provenance": "verified",
            }
        )
        self.source_id = source["source_id"]
        self.ledger = LearningLedger(self.ledger_path, self.catalog_path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def record(self, claim: str = "Serialize remote writes") -> dict[str, object]:
        return {
            "title": "Remote write safety",
            "domain": "repository-concurrency",
            "claim": claim,
            "evidence_status": "verified",
            "source_ids": [self.source_id],
            "decision": "Use current SHA and serialize writes",
            "outcome": "validated",
            "next_measurement": "Count conflict responses",
            "learned_at": "2026-09-28T01:59:00+00:00",
            "provenance": "verified",
            "failure_history": ["Parallel write can conflict"],
            "fallback_history": ["Re-read current SHA before retry"],
        }

    def test_learning_id_is_stable(self) -> None:
        self.assertEqual(
            learning_id("Repo", "Serialize writes"),
            learning_id(" repo ", "Serialize   writes"),
        )

    def test_add_is_idempotent_and_read_back_matches(self) -> None:
        first, created = self.ledger.add(self.record())
        second, created_again = self.ledger.add(self.record())
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first, second)
        self.assertEqual(self.ledger.find(first["learning_id"]), first)
        self.assertEqual(self.ledger.validate(), 1)

    def test_unknown_source_is_rejected(self) -> None:
        payload = self.record()
        payload["source_ids"] = ["src_missing"]
        with self.assertRaises(CatalogError):
            self.ledger.add(payload)

    def test_secret_or_pii_is_rejected(self) -> None:
        payload = self.record()
        payload["decision"] = "Contact person@example.com"
        with self.assertRaises(CatalogError):
            self.ledger.add(payload)

    def test_unknown_supersedes_is_rejected(self) -> None:
        payload = self.record()
        payload["supersedes"] = "learn_missing"
        with self.assertRaises(CatalogError):
            self.ledger.add(payload)

    def test_concurrent_duplicate_writes_create_one_learning(self) -> None:
        payload = self.record()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.ledger.add(payload), range(24)))
        self.assertEqual(sum(1 for _, created in results if created), 1)
        self.assertEqual(len(self.ledger.list()), 1)



    def test_persistence_gate_fails_closed_without_ledger_row(self) -> None:
        with self.assertRaises(CatalogError) as caught:
            persistence_gate(self.ledger, "FAIL_CLOSED_PERSISTENCE_GATE")
        self.assertIn("fail closed", str(caught.exception))

    def test_persistence_gate_fails_closed_when_source_missing(self) -> None:
        payload = self.record()
        payload["claim"] = "FAIL_CLOSED_PERSISTENCE_GATE requires a ledger row"
        payload["decision"] = "Reject markdown-only persistence"
        payload["source_ids"] = [self.source_id]
        self.ledger.add(payload)
        data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        data["learnings"][0]["source_ids"] = ["src_missing"]
        self.ledger_path.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(CatalogError) as caught:
            persistence_gate(self.ledger, "FAIL_CLOSED_PERSISTENCE_GATE")
        self.assertIn("source missing", str(caught.exception))

    def test_persistence_gate_read_back_passes(self) -> None:
        payload = self.record()
        payload["claim"] = "FAIL_CLOSED_PERSISTENCE_GATE requires a ledger row"
        payload["decision"] = "Reject markdown-only persistence"
        saved, created = self.ledger.add(payload)
        self.assertTrue(created)
        result = persistence_gate(self.ledger, "FAIL_CLOSED_PERSISTENCE_GATE")
        self.assertTrue(result["persisted"])
        self.assertEqual(result["learning_ids"], [saved["learning_id"]])
        self.assertEqual(self.ledger.find(saved["learning_id"])["learning_id"], saved["learning_id"])



    def test_optional_plan_tags_round_trip(self) -> None:
        payload = self.record("Preserve plan routing metadata")
        payload["plan_tags"] = ["Video/Shopify", "Sistem Geliştirmeleri"]
        payload["affected_plans"] = ["ignored when plan_tags present"]
        payload["status"] = "active"
        payload["use_count"] = 2
        payload["first_added_cycle"] = "2026-10-09T01:34+03:00"
        saved, created = self.ledger.add(payload)
        self.assertTrue(created)
        self.assertEqual(saved["plan_tags"], ["system", "video_shopify"])
        self.assertEqual(saved["use_count"], 2)
        self.assertEqual(saved["status"], "active")
        self.assertNotIn("use_count", self.ledger.add(self.record("Legacy row stays uncounted"))[0])

    def test_invalid_plan_tag_is_rejected(self) -> None:
        payload = self.record("Reject unknown plan tag")
        payload["plan_tags"] = ["Bilgi-Kutuphanesi"]
        with self.assertRaises(CatalogError):
            self.ledger.add(payload)

    def test_for_plan_uses_alias_and_skips_untagged(self) -> None:
        payload = self.record("Cross plan lookup")
        payload["plan_tags"] = ["Sistem Geliştirmeleri"]
        saved, created = self.ledger.add(payload)
        self.assertTrue(created)
        self.ledger.add(self.record("Untagged stays invisible to plan query"))
        found = self.ledger.for_plan("Sistem Geliştirmeleri")
        self.assertEqual([item["learning_id"] for item in found], [saved["learning_id"]])
        self.assertEqual(self.ledger.for_plan("system"), found)
        with self.assertRaises(CatalogError):
            self.ledger.for_plan("Bilgi Kütüphanesi")

if __name__ == "__main__":
    unittest.main()
