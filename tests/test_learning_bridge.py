from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, SourceCatalog
from scripts.learning_bridge import LearningLedger, learning_id


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


if __name__ == "__main__":
    unittest.main()
