import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
from scripts import tinyfish_event_bridge as b

ROOT = Path(__file__).resolve().parents[1]

class EventBridgeTests(unittest.TestCase):
    def test_event_key_is_deterministic(self):
        self.assertEqual(b.event_key("T1", "R1", "done"), b.event_key("T1", "R1", "done")); self.assertNotEqual(b.event_key("T1", "R1", "done"), b.event_key("T1", "R1", "failed"))
    def test_all_requesters_route_to_expected_channels(self):
        self.assertEqual(b.route_target("chatgpt").name, "shared-inbox.md"); self.assertEqual(b.route_target("grok").name, "chatgpt-to-grok.md"); self.assertEqual(b.route_target("gemini").name, "inbox-gemini.md"); self.assertEqual(b.route_target("meta").name, "inbox-meta.md")
        with self.assertRaises(ValueError): b.route_target("unknown")
    def test_terminal_replay_routes_once(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "route.md"; ledger = {"T1": {"task_id": "T1", "run_id": "R1", "requested_by": "grok", "mode": "browser", "status": "done", "routed_event_keys": []}}
            event = {"task_id": "T1", "run_id": "R1", "requested_by": "grok", "mode": "browser", "status": "done", "evidence": "messages/from-tinyfish.md", "blocker": "", "next_action": ""}
            with patch.object(b, "route_target", return_value=target): self.assertTrue(b.route_event(event, ledger)); self.assertFalse(b.route_event(event, ledger))
            self.assertEqual(target.read_text().count("task_id: T1"), 1)
    def test_normalize_preserves_run_id_when_remote_is_unknown(self):
        record = {"task_id": "T2", "run_id": "R2", "requested_by": "chatgpt", "mode": "browser", "status": "running"}; event = b.normalize_event(record, {"status": "unknown"}); self.assertEqual(event["run_id"], "R2"); self.assertEqual(event["status"], "running")
    def test_reconcile_503_is_retryable_and_preserves_run(self):
        record = {"task_id": "T3", "run_id": "R3", "requested_by": "meta", "mode": "browser", "status": "running", "routed_event_keys": []}; err = urllib.error.HTTPError("u", 503, "busy", {}, None)
        with patch.object(b, "remote_status", side_effect=err): updated = b.reconcile_record(record, "k")
        self.assertEqual(updated["status"], "retryable"); self.assertEqual(updated["run_id"], "R3"); self.assertEqual(updated["reason_code"], "transient")
    def test_reconcile_401_requires_human_action(self):
        record = {"task_id": "T4", "run_id": "R4", "requested_by": "gemini", "mode": "browser", "status": "running", "routed_event_keys": []}; err = urllib.error.HTTPError("u", 401, "no", {}, None)
        with patch.object(b, "remote_status", side_effect=err): updated = b.reconcile_record(record, "k")
        self.assertEqual(updated["status"], "blocked"); self.assertEqual(updated["reason_code"], "api-permission")
    def test_direct_script_entrypoint_runs_from_repo_root(self):
        env = dict(os.environ); env["TINYFISH_API_KEY"] = "test-key-not-secret"
        result = subprocess.run([sys.executable, "scripts/tinyfish_event_bridge.py"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

class WorkflowContractTests(unittest.TestCase):
    def test_senses_persists_run_ledger(self): self.assertIn("state/tinyfish-runs.json", (ROOT / ".github/workflows/tinyfish-senses.yml").read_text())
    def test_event_bridge_workflow_is_bounded_and_scoped(self):
        text = (ROOT / ".github/workflows/tinyfish-event-bridge.yml").read_text(); self.assertIn("group: tinyfish-event-bridge", text); self.assertIn("TINYFISH_API_KEY", text); self.assertIn("python3 scripts/tinyfish_event_bridge.py", text); self.assertIn("state/tinyfish-runs.json", text); self.assertIn("messages/from-tinyfish.md", text); self.assertNotIn("tinyfish_senses.py\n", text)

class ProtocolContractTests(unittest.TestCase):
    def test_protocol_documents_event_bridge_invariants(self):
        text = (ROOT / "PROTOCOL.md").read_text().lower(); self.assertIn("state/tinyfish-runs.json", text)
        for requester in ("chatgpt", "grok", "gemini", "meta"): self.assertIn(requester, text)
        self.assertIn("aynı task id", text); self.assertIn("ikinci browser", text)

if __name__ == "__main__": unittest.main()
