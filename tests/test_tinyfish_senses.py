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


if __name__ == "__main__":
    unittest.main()
