from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import task_events as te


class TaskEventLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ledger = Path(self.tmp.name) / "task_events.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_log_and_retry_are_idempotent(self):
        kwargs = dict(task_id="TSK-1", stage="task_started", actor="chatgpt",
                      status="in_progress", evidence="report RPT-1",
                      next_action="inspect", event_id="evt-1", path=self.ledger)
        first, created = te.log_event(**kwargs)
        second, created_again = te.log_event(**kwargs)
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first["event_id"], second["event_id"])
        self.assertEqual(len(te.read_ledger(self.ledger)["events"]), 1)

    def test_reused_event_id_with_different_payload_rejected(self):
        common = dict(task_id="TSK-1", stage="task_started", actor="chatgpt",
                      status="in_progress", event_id="evt-1", path=self.ledger)
        te.log_event(**common, evidence="one")
        with self.assertRaisesRegex(ValueError, "different payload"):
            te.log_event(**common, evidence="two")

    def test_source_found_requires_link_and_title(self):
        with self.assertRaisesRegex(ValueError, "source_title and source_url"):
            te.log_event(task_id="TSK-1", stage="source_found", actor="grok",
                         status="in_progress", path=self.ledger)
        event, _ = te.log_event(task_id="TSK-1", stage="source_found", actor="grok",
                                status="in_progress", source_title="Paper",
                                source_url="https://example.org/paper",
                                source_accessed="2026-09-27", path=self.ledger)
        self.assertEqual(event["source"]["title"], "Paper")

    def test_source_evaluation_requires_usefulness_reason(self):
        with self.assertRaisesRegex(ValueError, "usefulness reason"):
            te.log_event(task_id="TSK-1", stage="source_evaluated", actor="chatgpt",
                         status="not_useful", path=self.ledger)
        event, _ = te.log_event(task_id="TSK-1", stage="source_evaluated",
                                actor="chatgpt", status="not_useful",
                                reason="not current", path=self.ledger)
        self.assertEqual(event["reason"], "not current")

    def test_list_filters_by_task_and_keeps_audit_fields(self):
        for task_id in ("TSK-1", "TSK-2"):
            te.log_event(task_id=task_id, stage="reviewed", actor="grok",
                         status="reviewed", evidence="checked diff",
                         path=self.ledger)
        rows = te.list_events("TSK-1", path=self.ledger)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["actor"], "grok")
        self.assertEqual(rows[0]["stage"], "reviewed")
        self.assertTrue(rows[0]["at"])
        self.assertEqual(len(json.loads(self.ledger.read_text())["events"]), 2)

    def test_invalid_actor_and_stage_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid actor"):
            te.log_event(task_id="TSK-1", stage="task_started", actor="unknown",
                         status="in_progress", path=self.ledger)
        with self.assertRaisesRegex(ValueError, "invalid stage"):
            te.log_event(task_id="TSK-1", stage="unknown", actor="chatgpt",
                         status="in_progress", path=self.ledger)


if __name__ == "__main__":
    unittest.main()
