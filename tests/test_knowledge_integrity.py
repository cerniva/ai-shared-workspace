"""Integrity spec 2026-10-10 (intake/chatgpt/2026-10-10-knowledge-integrity-spec.md)."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, SourceCatalog, source_id
from scripts.knowledge_promote import _check_superset, apply_promotions

ROOT = Path(__file__).resolve().parents[1]
SOURCE = {
    "source_name": "Official docs",
    "canonical": "https://example.com/reports",
    "category": "test",
    "purpose": "Fixture source",
    "evidence_tier": "official",
    "access_status": "verified-public",
    "cost_quota": "free",
    "reliability_limits": "Fixture only",
    "discovered_at": "2026-10-10T00:00:00+00:00",
    "provenance": "verified",
}


def learning(sid: str) -> dict:
    return {
        "title": "Fixture", "domain": "test-domain", "claim": "Fixture claim.",
        "evidence_status": "verified", "decision": "FIXTURE_GATE: test.", "outcome": "validated",
        "next_measurement": "n/a", "learned_at": "2026-10-10T00:00:00+00:00", "provenance": "verified",
        "source_ids": [sid], "failure_history": [], "fallback_history": [], "supersedes": None,
    }


class IntegrityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "knowledge" / "promotions").mkdir(parents=True)
        self.catalog = self.root / "knowledge" / "source_catalog.json"
        self.ledger = self.root / "knowledge" / "learning_ledger.json"
        SourceCatalog(self.catalog).add(dict(SOURCE, canonical="https://example.com/existing"))
        self.sid = source_id("https://example.com/reports")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def stage(self, doc, name: str) -> None:
        text = doc if isinstance(doc, str) else json.dumps(doc)
        (self.root / "knowledge" / "promotions" / name).write_text(text, encoding="utf-8")

    def snapshot(self):
        return (self.catalog.read_bytes(), self.ledger.read_bytes() if self.ledger.exists() else None)

    def assert_rolled_back(self, before) -> None:
        with self.assertRaises(CatalogError):
            apply_promotions(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_mixed_valid_and_invalid_batch_writes_nothing(self) -> None:
        # Rule 4: a.json is valid and sorts first; before, it was persisted
        # even though b.json failed.
        self.stage({"source": SOURCE, "learning": learning(self.sid)}, "a.json")
        self.stage({"learning": learning("src_missing00000000")}, "b.json")
        self.assert_rolled_back(self.snapshot())

    def test_invalid_staged_id_in_later_file_rolls_back(self) -> None:
        self.stage({"source": SOURCE}, "a.json")
        self.stage({"source": dict(SOURCE, canonical="https://example.com/x", source_id="src_bad")}, "b.json")
        self.assert_rolled_back(self.snapshot())

    def test_malformed_json_fails_closed(self) -> None:
        self.stage({"source": SOURCE}, "a.json")
        self.stage("{not json", "b.json")
        self.assert_rolled_back(self.snapshot())

    def test_schema_version_mismatch_fails_closed(self) -> None:
        self.stage({"schema_version": 2, "source": SOURCE}, "a.json")
        self.assert_rolled_back(self.snapshot())

    def test_conflicting_duplicate_across_files_fails_closed(self) -> None:
        self.stage({"source": SOURCE}, "a.json")
        self.stage({"source": dict(SOURCE, purpose="Different purpose")}, "b.json")
        self.assert_rolled_back(self.snapshot())

    def test_identical_duplicate_is_idempotent(self) -> None:
        self.stage({"source": SOURCE}, "a.json")
        self.stage({"source": SOURCE}, "b.json")
        report = apply_promotions(self.root)
        self.assertEqual(report["sources_created"], [self.sid])

    def test_secret_in_gate_or_row_rejected(self) -> None:
        self.stage({"source": dict(SOURCE, purpose="key ghp_" + "a" * 36)}, "a.json")
        self.assert_rolled_back(self.snapshot())

    def test_secret_in_gate_rejected(self) -> None:
        self.stage({"gates": ["github_pat_" + "A" * 40]}, "a.json")
        self.assert_rolled_back(self.snapshot())

    def test_superset_check_detects_lost_rows(self) -> None:
        with self.assertRaises(CatalogError):
            _check_superset({"sources": {"a", "b"}, "learnings": set()}, {"sources": {"a"}, "learnings": set()})
        _check_superset({"sources": {"a"}, "learnings": {"x"}}, {"sources": {"a", "b"}, "learnings": {"x"}})

    def test_success_reports_changed_files_and_reads_back(self) -> None:
        self.stage({"source": SOURCE, "learning": learning(self.sid)}, "a.json")
        report = apply_promotions(self.root)
        self.assertEqual(sorted(report["changed_files"]), ["learning_ledger.json", "source_catalog.json"])
        self.assertEqual(apply_promotions(self.root)["changed_files"], [])

    def test_real_repo_promotions_apply_and_are_idempotent(self) -> None:
        # Rule 7/10: existing canonical rows are kept; a re-run changes nothing.
        work = self.root / "repo"
        shutil.copytree(ROOT / "knowledge", work / "knowledge")
        before = json.loads((work / "knowledge" / "source_catalog.json").read_text(encoding="utf-8"))
        first = apply_promotions(work)
        self.assertGreaterEqual(first["source_count"], len(before["sources"]))
        snap = ((work / "knowledge" / "source_catalog.json").read_bytes(), (work / "knowledge" / "learning_ledger.json").read_bytes())
        second = apply_promotions(work)
        self.assertEqual(second["changed_files"], [])
        self.assertEqual(snap, ((work / "knowledge" / "source_catalog.json").read_bytes(), (work / "knowledge" / "learning_ledger.json").read_bytes()))


if __name__ == "__main__":
    unittest.main()
