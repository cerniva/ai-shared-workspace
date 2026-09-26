import unittest
from scripts import tinyfish_senses as t


class ParseTests(unittest.TestCase):
    def test_legacy_defaults_to_fetch(self):
        task = t.parse_task("status: queued\nid: a\nfrom: chatgpt\nurls: https://example.com")
        self.assertEqual(task["mode"], "fetch")
        self.assertEqual(task["urls"], ["https://example.com"])

    def test_browser_multiline_goal(self):
        task = t.parse_task(
            "status: queued\nid: b\nfrom: grok\nmode: browser\n"
            "url: https://example.com\ngoal: |\n  Open pricing\n  and report plans"
        )
        self.assertEqual(task["requested_by"], "grok")
        self.assertEqual(task["url"], "https://example.com")
        self.assertEqual(task["goal"], "Open pricing\nand report plans")

    def test_validation_rejects_bad_mode_and_incomplete_browser(self):
        ok, _ = t.validate_task({"mode": "weird"})
        self.assertFalse(ok)
        ok, _ = t.validate_task({"mode": "browser", "url": "", "goal": ""})
        self.assertFalse(ok)


class BrowserTests(unittest.TestCase):
    def test_payload_is_bounded(self):
        task = {"mode": "browser", "url": "https://example.com", "goal": "Open pricing"}
        payload = t.build_browser_payload(task)
        self.assertEqual(payload["url"], "https://example.com")
        self.assertEqual(payload["goal"], "Open pricing")
        self.assertEqual(payload["browser_profile"], "lite")
        self.assertEqual(payload["agent_config"]["max_steps"], 50)
        self.assertEqual(payload["agent_config"]["max_duration_seconds"], 300)

    def test_prohibited_goals_block(self):
        goals = ["buy this product", "publish this post", "delete my account", "change password", "submit secret key", "bypass 2FA", "solve CAPTCHA", "login to admin"]
        for goal in goals:
            self.assertTrue(t.browser_block_reason({"mode": "browser", "goal": goal}), goal)

    def test_fetch_not_browser_payload(self):
        with self.assertRaises(ValueError):
            t.build_browser_payload({"mode": "fetch", "url": "https://example.com", "goal": "click"})


if __name__ == "__main__":
    unittest.main()
