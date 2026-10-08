from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, SourceCatalog, source_id
from scripts.knowledge_promote import apply_promotions
from scripts.learning_bridge import LearningLedger, learning_id

SOURCE = {
    "source_name": "Official docs",
    "canonical": "https://example.com/reports",
    "category": "test",
    "purpose": "Fixture source",
    "evidence_tier": "official",
    "access_status": "verified-public",
    "cost_quota": "free",
    "reliability_limits": "Fixture only",
    "discovered_at": "2026-10-08T04:50:00+00:00",
    "provenance": "verified",
}


def learning(sid: str) -> dict[str, object]:
    return {
        "title": "Header-only gate",
        "domain": "test-domain",
        "claim": "Header-only reports mean no data, not failure.",
        "evidence_status": "verified",
        "decision": "HEADER_ONLY_TEST_GATE: classify as VALID_NO_DATA.",
        "outcome": "validated",
        "next_measurement": "Count rows per report.",
        "learned_at": "2026-10-08T04:50:00+00:00",
        "provenance": "verified",
        "source_ids": [sid],
        "failure_history": [],
        "fallback_history": [],
        "supersedes": None,
    }


class KnowledgePromoteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "knowledge" / "promotions").mkdir(parents=True)
        self.catalog = self.root / "knowledge" / "source_catalog.json"
        self.ledger = self.root / "knowledge" / "learning_ledger.json"
        existing = dict(SOURCE, canonical="https://example.com/existing", source_name="Existing")
        SourceCatalog(self.catalog).add(existing)
        self.sid = source_id("https://example.com/reports")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def stage(self, doc: dict[str, object], name: str = "p.json") -> None:
        (self.root / "knowledge" / "promotions" / name).write_text(json.dumps(doc), encoding="utf-8")

    def test_applies_staged_rows_and_keeps_existing(self) -> None:
        lrn = learning(self.sid)
        lid = learning_id(str(lrn["domain"]), str(lrn["claim"]))
        self.stage({
            "source": dict(SOURCE, source_id=self.sid),
            "learning": dict(lrn, learning_id=lid),
            "validators": {"gate": "HEADER_ONLY_TEST_GATE"},
        })
        report = apply_promotions(self.root)
        self.assertEqual(report["sources_created"], [self.sid])
        self.assertEqual(report["learnings_created"], [lid])
        self.assertEqual(report["source_count"], 2)
        self.assertEqual(report["learning_count"], 1)
        self.assertIsNotNone(LearningLedger(self.ledger, self.catalog).find(lid))

    def test_second_run_is_noop(self) -> None:
        self.stage({"source": SOURCE, "learning": learning(self.sid)})
        apply_promotions(self.root)
        before = (self.catalog.read_bytes(), self.ledger.read_bytes())
        report = apply_promotions(self.root)
        self.assertEqual(report["sources_created"], [])
        self.assertEqual(report["learnings_created"], [])
        self.assertEqual(before, (self.catalog.read_bytes(), self.ledger.read_bytes()))

    def test_staged_id_mismatch_fails_closed(self) -> None:
        self.stage({"source": SOURCE, "learning": dict(learning(self.sid), learning_id="learn_wrong")})
        with self.assertRaises(CatalogError):
            apply_promotions(self.root)

    def test_learning_with_unknown_source_fails_closed(self) -> None:
        self.stage({"learning": learning("src_doesnotexist000")})
        with self.assertRaises(CatalogError):
            apply_promotions(self.root)

    def test_missing_gate_fails_closed(self) -> None:
        self.stage({"source": SOURCE, "learning": learning(self.sid), "gates": ["NOT_PRESENT_GATE"]})
        with self.assertRaises(CatalogError):
            apply_promotions(self.root)


if __name__ == "__main__":
    unittest.main()
