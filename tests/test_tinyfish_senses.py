import tempfile
import unittest
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
