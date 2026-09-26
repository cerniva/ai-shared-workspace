"""chatgpt-to-gemini letters must land in inbox-gemini."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.route_gemini_inbox as route


class RouteGeminiInboxTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.msg = base / "messages"
        self.msg.mkdir()
        self._letter = route.LETTER
        self._inbox = route.INBOX
        route.LETTER = self.msg / "chatgpt-to-gemini.md"
        route.INBOX = self.msg / "inbox-gemini.md"

    def tearDown(self):
        route.LETTER = self._letter
        route.INBOX = self._inbox
        self.tmp.cleanup()

    def test_open_letter_routes_once(self):
        route.LETTER.write_text(
            "\n---\nid: MSG-test-1\nfrom: chatgpt\nto: gemini\n"
            "created_at: 2026-09-26T18:00:00+03:00\nproject: workspace\n"
            "status: open\n---\n\nPlease analyze this video.\n",
            encoding="utf-8",
        )
        route.INBOX.write_text("# Inbox\n\n## TASK\nstatus: idle\n", encoding="utf-8")
        first = route.route()
        self.assertTrue(first.startswith("routed:MSG-test-1"))
        text = route.INBOX.read_text(encoding="utf-8")
        self.assertIn("status: queued", text)
        self.assertIn("MSG-test-1", text)
        self.assertEqual(route.route(), "noop:already-routed:MSG-test-1")

    def test_done_letter_noop(self):
        route.LETTER.write_text(
            "\n---\nid: MSG-done\nfrom: chatgpt\nto: gemini\nstatus: done\n---\n\nold\n",
            encoding="utf-8",
        )
        self.assertEqual(route.route(), "noop:no-actionable-letter")


if __name__ == "__main__":
    unittest.main()
