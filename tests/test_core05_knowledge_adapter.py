from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.core05_knowledge_adapter import CORE05_DOMAIN, Core05KnowledgeAdapter


class Core05KnowledgeAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.adapter = Core05KnowledgeAdapter(
            catalog_path=root / "source_catalog.json",
            ledger_path=root / "learning_ledger.json",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_source_and_learning_read_write_read_back(self) -> None:
        source, created = self.adapter.record_source({
            "source_name": "GitHub Actions docs",
            "canonical": "https://docs.github.com/en/actions?utm_source=core05#overview",
            "category": "ci-cd",
            "purpose": "CORE-05 CI verification",
            "evidence_tier": "official",
            "access_status": "verified-public",
            "cost_quota": "free public documentation",
            "reliability_limits": "Documentation does not prove repository runtime state",
            "discovered_at": "2026-09-28T13:30:00+00:00",
            "provenance": "verified",
            "last_successful_use": "2026-09-28T13:30:00+00:00",
        })
        self.assertTrue(created)
        self.assertEqual(source["canonical"], "https://docs.github.com/en/actions")
        self.assertEqual(self.adapter.read_source(source["source_id"]), source)

        duplicate, created_again = self.adapter.record_source({
            "source_name": "GitHub Actions docs alias",
            "canonical": "https://DOCS.GITHUB.COM:443/en/actions/?utm_campaign=duplicate",
            "category": "ci-cd",
            "purpose": "Alias dedup verification",
            "evidence_tier": "official",
            "access_status": "verified-public",
            "cost_quota": "free public documentation",
            "reliability_limits": "Documentation does not prove repository runtime state",
            "discovered_at": "2026-09-28T13:31:00+00:00",
            "provenance": "verified",
        })
        self.assertFalse(created_again)
        self.assertEqual(duplicate["source_id"], source["source_id"])

        learning, learning_created = self.adapter.record_learning({
            "title": "CORE-05 shared bridge smoke test",
            "claim": "CORE-05 can persist a source-linked learning and read it back",
            "evidence_status": "verified",
            "decision": "Use the shared catalog and ledger instead of a plan-local duplicate",
            "outcome": "validated",
            "next_measurement": "CI must pass this integration test",
            "learned_at": "2026-09-28T13:32:00+00:00",
            "provenance": "verified",
            "source_ids": [source["source_id"]],
            "failure_history": [],
            "fallback_history": [],
        })
        self.assertTrue(learning_created)
        self.assertEqual(learning["domain"], CORE05_DOMAIN)
        self.assertEqual(self.adapter.read_learning(learning["learning_id"]), learning)
        self.assertTrue(self.adapter.validate()["valid"])


if __name__ == "__main__":
    unittest.main()
