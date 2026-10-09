import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import SourceCatalog
from scripts.learning_bridge import LearningLedger


class ForPlanStatusFilterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        catalog = root / "source_catalog.json"
        source, _ = SourceCatalog(catalog).add({
            "source_name": "Official docs", "canonical": "https://example.com/docs",
            "category": "test", "purpose": "Test source", "evidence_tier": "official",
            "access_status": "verified-public", "cost_quota": "free",
            "reliability_limits": "Fixture only", "discovered_at": "2026-10-09T00:00:00+00:00",
            "provenance": "verified",
        })
        self.source_id = source["source_id"]
        self.ledger = LearningLedger(root / "learning_ledger.json", catalog)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def add(self, claim: str, **extra):
        record = {
            "title": claim, "domain": "plan-filter", "claim": claim,
            "evidence_status": "verified", "source_ids": [self.source_id],
            "decision": "d", "outcome": "validated", "next_measurement": "m",
            "learned_at": "2026-10-09T00:00:00+00:00", "provenance": "verified",
            "plan_tags": ["finance"], **extra,
        }
        saved, _ = self.ledger.add(record)
        return saved["learning_id"]

    def test_inactive_and_superseded_status_are_excluded(self) -> None:
        active = self.add("active claim")
        self.add("inactive claim", status="inactive")
        self.add("superseded claim", status="superseded")
        self.assertEqual([r["learning_id"] for r in self.ledger.for_plan("Finans")], [active])

    def test_row_replaced_via_supersedes_is_excluded(self) -> None:
        old = self.add("old claim")
        new = self.add("new claim", supersedes=old)
        self.assertEqual([r["learning_id"] for r in self.ledger.for_plan("finance")], [new])

    def test_untagged_status_default_is_active(self) -> None:
        only = self.add("plain claim")
        self.assertEqual([r["learning_id"] for r in self.ledger.for_plan("finance")], [only])


if __name__ == "__main__":
    unittest.main()
