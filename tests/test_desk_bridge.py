"""Tests for scripts/desk_bridge.py — aliases, channels, body limits, CLI helpers."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import scripts.desk_bridge as db


class DeskBridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.msg_dir = self.base / "messages"
        self.msg_dir.mkdir()
        # Override CHANNELS paths only; keep expected_from / expected_to semantics
        self._orig = dict(db.CHANNELS)
        db.CHANNELS = {
            "grok-to-chatgpt": (
                self.msg_dir / "grok-to-chatgpt.md",
                frozenset({"grok", "grok-bot"}),
                "chatgpt",
            ),
            "chatgpt-to-grok": (
                self.msg_dir / "chatgpt-to-grok.md",
                "chatgpt",
                "grok",
            ),
            "inbox-gemini": (self.msg_dir / "inbox-gemini.md", None, "gemini"),
            "gemini-to-chatgpt": (
                self.msg_dir / "gemini-to-chatgpt.md",
                "gemini",
                "chatgpt",
            ),
            "chatgpt-to-gemini": (
                self.msg_dir / "chatgpt-to-gemini.md",
                "chatgpt",
                "gemini",
            ),
        }

    def tearDown(self):
        db.CHANNELS = self._orig
        self.tmp.cleanup()

    def test_grok_bot_alias_accepted(self):
        mid = db.append_message(
            "grok-to-chatgpt",
            "grok-bot",
            "chatgpt",
            "alias ok\nNext-action: ack.",
        )
        self.assertTrue(mid.startswith("MSG-"))
        text = (self.msg_dir / "grok-to-chatgpt.md").read_text(encoding="utf-8")
        self.assertIn("from: grok-bot", text)
        self.assertIn(mid, text)

    def test_grok_canonical_still_accepted(self):
        mid = db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "canonical from=grok"
        )
        self.assertIn("grok", mid)

    def test_wrong_from_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            db.append_message(
                "grok-to-chatgpt", "chatgpt", "chatgpt", "should fail"
            )
        self.assertIn("requires from", str(ctx.exception))

    def test_chatgpt_to_gemini_append(self):
        mid = db.append_message(
            "chatgpt-to-gemini",
            "chatgpt",
            "gemini",
            "kanal eklendi\nNext-action: verify.",
        )
        path = self.msg_dir / "chatgpt-to-gemini.md"
        self.assertTrue(path.exists())
        text = path.read_text(encoding="utf-8")
        self.assertIn(mid, text)
        self.assertIn("from: chatgpt", text)
        self.assertIn("to: gemini", text)

    def test_body_empty_rejected(self):
        with self.assertRaises(ValueError) as ctx:
            db.append_message("grok-to-chatgpt", "grok", "chatgpt", "   \n  ")
        self.assertIn("1..12", str(ctx.exception))

    def test_body_too_long_rejected(self):
        body = "\n".join(f"line {i}" for i in range(13))
        with self.assertRaises(ValueError) as ctx:
            db.append_message("grok-to-chatgpt", "grok", "chatgpt", body)
        self.assertIn("1..12", str(ctx.exception))

    def test_body_twelve_lines_ok(self):
        body = "\n".join(f"line {i}" for i in range(12))
        mid = db.append_message("grok-to-chatgpt", "grok", "chatgpt", body)
        self.assertTrue(mid.startswith("MSG-"))

    def test_wrong_to_rejected(self):
        with self.assertRaises(ValueError):
            db.append_message("grok-to-chatgpt", "grok", "gemini", "bad to")

    def test_invalid_status_rejected(self):
        with self.assertRaises(ValueError):
            db.append_message(
                "grok-to-chatgpt",
                "grok",
                "chatgpt",
                "x",
                status="wip",
            )

    def test_latest_and_open(self):
        db.append_message(
            "grok-to-chatgpt",
            "grok",
            "chatgpt",
            "first",
            status="done",
        )
        mid2 = db.append_message(
            "grok-to-chatgpt",
            "grok-bot",
            "chatgpt",
            "second open",
            status="open",
        )
        latest = db.latest_message("grok-to-chatgpt")
        self.assertIn(mid2, latest)
        self.assertIn("second open", latest)
        self.assertIn("status: open", latest)
        opens = db.open_message_ids("grok-to-chatgpt")
        self.assertEqual(opens, [mid2])

    def test_list_channels_includes_chatgpt_to_gemini(self):
        text = db.list_channels()
        self.assertIn("chatgpt-to-gemini", text)
        self.assertIn("grok-bot", text)


if __name__ == "__main__":
    unittest.main()
