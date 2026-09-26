import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import tinyfish_senses as t


class ParseTests(unittest.TestCase):
    def test_legacy_defaults_to_fetch(self):
        task = t.parse_task("status: queued\nid: a\nfrom: chatgpt\nurls: https://example.com")
        self.assertEqual(task["mode"], "fetch")
        self.assertEqual(task["urls"], ["https://example.com"])

    def test_browser_multiline_goal(self):
        task = t.parse_task("status: queued\nid: b\nfrom: grok\nmode: browser\nurl: https://example.com\ngoal: |\n  Open pricing\n  and report plans")
        self.assertEqual(task["requested_by"], "grok")
        self.assertEqual(task["url"], "https://example.com")
        self.assertEqual(task["goal"], "Open pricing\nand report plans")

    def test_validation_rejects_bad_mode_and_incomplete_browser(self):
        ok, _ = t.validate_task({"mode": "weird"}); self.assertFalse(ok)
        ok, _ = t.validate_task({"mode": "browser", "url": "", "goal": ""}); self.assertFalse(ok)


class BrowserTests(unittest.TestCase):
    def test_payload_is_bounded(self):
        task = {"mode": "browser", "url": "https://example.com", "goal": "Open pricing"}
        payload = t.build_browser_payload(task)
        self.assertEqual(payload["browser_profile"], "lite")
        self.assertEqual(payload["agent_config"]["max_steps"], 50)
        self.assertEqual(payload["agent_config"]["max_duration_seconds"], 300)

    def test_prohibited_goals_block(self):
        for goal in ["buy this product", "publish this post", "delete my account", "change password", "submit secret key", "bypass 2FA", "solve CAPTCHA", "login to admin"]:
            self.assertTrue(t.browser_block_reason({"mode": "browser", "goal": goal}), goal)

    def test_fetch_not_browser_payload(self):
        with self.assertRaises(ValueError):
            t.build_browser_payload({"mode": "fetch", "url": "https://example.com", "goal": "click"})


class ResultTests(unittest.TestCase):
    def test_result_metadata_and_bound(self):
        with tempfile.TemporaryDirectory() as d:
            old = t.OUT; t.OUT = Path(d) / "out.md"
            try:
                t.append_result({"id": "abc", "requested_by": "grok", "mode": "fetch"}, "done", {"x": "z" * 10000})
                text = t.OUT.read_text()
                self.assertIn("task_id: abc", text); self.assertIn("requested_by: grok", text); self.assertIn("mode: fetch", text)
                self.assertLess(len(text), 6000)
            finally:
                t.OUT = old

    def test_blocker_dedupe(self):
        with tempfile.TemporaryDirectory() as d:
            old = t.ACTION; t.ACTION = Path(d) / "a.md"
            try:
                self.assertTrue(t.append_action_once("TinyFish", "missing-secret", "missing"))
                self.assertFalse(t.append_action_once("TinyFish", "missing-secret", "missing"))
                self.assertTrue(t.append_action_once("TinyFish", "credits", "credits"))
                self.assertEqual(t.ACTION.read_text().count("status: open"), 2)
            finally:
                t.ACTION = old


class RoutingTests(unittest.TestCase):
    def test_routes_fetch_and_browser_once(self):
        with patch.object(t, "fetch", return_value={"ok": 1}) as fetch_call, patch.object(t, "run_browser", return_value={"ok": 2}) as browser_call:
            status, _, _ = t.execute_task({"mode": "fetch", "urls": ["https://example.com"]}, "k")
            self.assertEqual(status, "done"); fetch_call.assert_called_once(); browser_call.assert_not_called()
        with patch.object(t, "fetch", return_value={"ok": 1}) as fetch_call, patch.object(t, "run_browser", return_value={"ok": 2}) as browser_call:
            status, _, _ = t.execute_task({"mode": "browser", "url": "https://example.com", "goal": "read pricing"}, "k")
            self.assertEqual(status, "done"); browser_call.assert_called_once(); fetch_call.assert_not_called()

    def test_http_classification(self):
        self.assertEqual(t.classify_http_status(401)[0], "api-permission")
        self.assertEqual(t.classify_http_status(403)[0], "api-permission")
        self.assertEqual(t.classify_http_status(402)[0], "credits-plan")
        self.assertEqual(t.classify_http_status(429)[0], "transient")
        self.assertEqual(t.classify_http_status(503)[0], "transient")


class LedgerTests(unittest.TestCase):
    def test_missing_ledger_loads_empty(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(t.load_ledger(Path(d) / "missing.json"), {})

    def test_record_start_and_terminal_preserve_identity(self):
        ledger = {}
        record = t.record_run_start(ledger, {"id": "B1", "requested_by": "grok", "mode": "browser"}, "run-7")
        self.assertEqual(record["status"], "running")
        self.assertEqual(record["run_id"], "run-7")
        self.assertEqual(record["routed_event_keys"], [])
        done = t.record_terminal(ledger, "B1", "done", "")
        self.assertEqual(done["run_id"], "run-7")
        self.assertEqual(done["status"], "done")

    def test_running_browser_is_not_started_twice(self):
        task = {"id": "B1", "requested_by": "chatgpt", "mode": "browser", "url": "https://example.com", "goal": "read pricing"}
        ledger = {"B1": {"task_id": "B1", "requested_by": "chatgpt", "mode": "browser", "status": "running", "run_id": "run-1", "updated_at": "x", "last_error": "", "routed_event_keys": []}}
        with patch.object(t, "run_browser") as call:
            status, data, reason = t.execute_task(task, "k", ledger=ledger)
        self.assertEqual(status, "running")
        self.assertEqual(data["run_id"], "run-1")
        call.assert_not_called()

    def test_terminal_task_is_not_executed_again(self):
        task = {"id": "F1", "requested_by": "chatgpt", "mode": "fetch", "urls": ["https://example.com"]}
        ledger = {"F1": {"task_id": "F1", "requested_by": "chatgpt", "mode": "fetch", "status": "done", "run_id": "", "updated_at": "x", "last_error": "", "routed_event_keys": []}}
        with patch.object(t, "fetch") as call:
            status, _, _ = t.execute_task(task, "k", ledger=ledger)
        self.assertEqual(status, "done")
        call.assert_not_called()

    def test_transient_error_records_retryable_without_user_blocker(self):
        task = {"id": "B2", "requested_by": "grok", "mode": "browser", "url": "https://example.com", "goal": "read pricing"}
        ledger = {}
        err = __import__("urllib.error").error.HTTPError("u", 503, "busy", {}, None)
        with patch.object(t, "run_browser", side_effect=err), patch.object(t, "append_action_once") as action:
            status, data, _ = t.execute_task(task, "k", ledger=ledger)
        self.assertEqual(status, "retryable")
        self.assertEqual(data["reason_code"], "transient")
        self.assertEqual(ledger["B2"]["status"], "retryable")
        action.assert_not_called()


if __name__ == "__main__":
    unittest.main()
