"""Fail-closed tests for the offline Reporting API checkpoint decision."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, DEFAULT_CATALOG
from scripts.learning_bridge import DEFAULT_LEDGER
from scripts import youtube_reporting_checkpoint as gate


def report(rid, created, start="2026-10-20T00:00:00Z",
           status="persisted_readback_verified"):
    return {"id": rid, "jobId": "job1", "startTime": start,
            "endTime": "2026-10-21T00:00:00Z",
            "createTime": created, "import_status": status}


def batch(*reports, complete=True, readback=True):
    return {"previous_checkpoint": "2026-10-20T10:00:00Z",
            "reports": list(reports), "pagination_complete": complete,
            "batch_index_readback_verified": readback}


class CheckpointTests(unittest.TestCase):
    def test_actual_decision_contains_applied_learning_and_proposed_cursor(self):
        result = gate.evaluate_batch(batch(report("r1", "2026-10-21T12:00:00Z")))
        self.assertEqual(result["decision_status"], "ADVANCE_READY")
        self.assertEqual(result["decision_before"]["createdAfter"], "2026-10-20T10:00:00Z")
        self.assertEqual(result["decision_after_proposed"]["createdAfter"], "2026-10-21T12:00:00Z")
        self.assertEqual(result["applied_learning_ids"], [gate.LEARNING_ID])
        self.assertEqual(result["source_ids"], [gate.SOURCE_ID])
        self.assertFalse(result["checkpoint_committed"])
        self.assertFalse(result["production_channel_access"])

    def test_partial_page_holds_cursor(self):
        result = gate.evaluate_batch(batch(report("r1", "2026-10-21T12:00:00Z"), complete=False))
        self.assertEqual(result["decision_status"], "HOLD_INCOMPLETE_PAGINATION")
        self.assertEqual(result["decision_after_proposed"], result["decision_before"])

    def test_unverified_import_or_batch_readback_holds(self):
        for b in (batch(report("r1", "2026-10-21T12:00:00Z", status="failed")),
                  batch(report("r1", "2026-10-21T12:00:00Z"), readback=False)):
            with self.subTest(b=b):
                result = gate.evaluate_batch(b)
                self.assertEqual(result["decision_status"], "HOLD_UNVERIFIED_IMPORT")
                self.assertEqual(result["decision_after_proposed"], result["decision_before"])

    def test_backfill_replaces_old_period_not_sum(self):
        old = report("old", "2026-10-20T11:00:00Z", status="unprocessed")
        new = report("new", "2026-10-21T12:00:00Z")
        result = gate.evaluate_batch(batch(old, new))
        self.assertEqual(result["selected_report_ids"], ["new"])
        self.assertEqual(result["decision_status"], "ADVANCE_READY")

    def test_duplicate_report_id_is_idempotent(self):
        row = report("r1", "2026-10-21T12:00:00Z")
        result = gate.evaluate_batch(batch(row, dict(row)))
        self.assertEqual(result["selected_report_ids"], ["r1"])

    def test_conflicting_id_or_ambiguous_backfill_rejected(self):
        row = report("r1", "2026-10-21T12:00:00Z")
        changed = dict(row, createTime="2026-10-22T12:00:00Z")
        with self.assertRaisesRegex(ValueError, "CONFLICTING_REPORT_ID"):
            gate.evaluate_batch(batch(row, changed))
        with self.assertRaisesRegex(ValueError, "AMBIGUOUS_BACKFILL"):
            gate.evaluate_batch(batch(row, dict(row, id="r2")))

    def test_no_new_reports_never_moves_checkpoint(self):
        result = gate.evaluate_batch(batch())
        self.assertEqual(result["decision_status"], "NO_NEW_REPORTS")
        self.assertEqual(result["decision_after_proposed"], result["decision_before"])

    def test_missing_active_learning_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            ledger = Path(folder) / "ledger.json"
            catalog = Path(folder) / "catalog.json"
            shutil.copy(DEFAULT_LEDGER, ledger)
            shutil.copy(DEFAULT_CATALOG, catalog)
            data = json.loads(ledger.read_text(encoding="utf-8"))
            for item in data["learnings"]:
                if item.get("learning_id") == gate.LEARNING_ID:
                    item["status"] = "inactive"
            ledger.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(CatalogError, "bridge_failure"):
                gate.evaluate_batch(batch(), ledger, catalog)

    def test_invalid_timestamps_fail_closed(self):
        with self.assertRaises(ValueError):
            gate.evaluate_batch(batch(report("r1", "2026-10-21T12:00:00")))
        with self.assertRaises(ValueError):
            gate.evaluate_batch(batch(report("r1", "bad timestamp")))

    def test_cli_emits_applied_learning_ids_in_real_decision_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "batch.json"
            path.write_text(json.dumps(batch(report("r1", "2026-10-21T12:00:00Z"))), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, "-m", "scripts.youtube_reporting_checkpoint", str(path)],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            output = json.loads(proc.stdout)
            self.assertEqual(output["applied_learning_ids"], [gate.LEARNING_ID])
            self.assertEqual(output["decision_status"], "ADVANCE_READY")
            self.assertFalse(output["checkpoint_committed"])


if __name__ == "__main__":
    unittest.main()
