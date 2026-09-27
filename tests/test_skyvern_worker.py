import unittest

from browser_worker.policy import PolicyViolation
from browser_worker.skyvern_worker import adapt_task


class SkyvernWorkerAdapterTests(unittest.TestCase):
    def test_explicit_task_is_preserved(self):
        url, prompt = adapt_task({
            "url": "https://example.com",
            "goal": "Read the public page title",
        })
        self.assertEqual(url, "https://example.com")
        self.assertEqual(prompt, "Read the public page title")

    def test_planner_steps_are_adapted(self):
        url, prompt = adapt_task({
            "id": "ai-browser",
            "steps": [
                {"action": "goto", "url": "https://example.com"},
                {"action": "extract", "selector": "title"},
            ],
        })
        self.assertEqual(url, "https://example.com")
        self.assertIn("extract 'title'", prompt)
        self.assertIn("Do not click", prompt)

    def test_interactive_steps_fail_closed(self):
        with self.assertRaisesRegex(PolicyViolation, "read-only"):
            adapt_task({
                "steps": [
                    {"action": "goto", "url": "https://example.com"},
                    {"action": "click", "text": "Continue"},
                ]
            })

    def test_multiple_goto_urls_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly one goto URL"):
            adapt_task({
                "steps": [
                    {"action": "goto", "url": "https://example.com"},
                    {"action": "goto", "url": "https://example.org"},
                ]
            })


if __name__ == "__main__":
    unittest.main()
