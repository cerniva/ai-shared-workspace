"""Tests for scripts/desk_bridge.py — aliases, channels, body limits, CLI helpers."""
from __future__ import annotations

import datetime as dt
import re
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
        self._orig_inbox_path = db.INBOX_READ_PATH
        self._orig_delivery_path = db.DELIVERY_PATH
        self.state_dir = self.base / "state"
        self.state_dir.mkdir()
        db.INBOX_READ_PATH = self.state_dir / "inbox_read.json"
        db.DELIVERY_PATH = self.state_dir / "message_delivery.json"

    def tearDown(self):
        db.CHANNELS = self._orig
        db.INBOX_READ_PATH = self._orig_inbox_path
        db.DELIVERY_PATH = self._orig_delivery_path
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
        self.assertIn("invalid status", str(ctx.exception))

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

    def test_idempotent_append_returns_same_id(self):
        body = "idempotent body\nNext-action: none."
        mid1 = db.append_message("grok-to-chatgpt", "grok-bot", "chatgpt", body)
        mid2 = db.append_message("grok-to-chatgpt", "grok-bot", "chatgpt", body)
        self.assertEqual(mid1, mid2)
        text = (self.msg_dir / "grok-to-chatgpt.md").read_text(encoding="utf-8")
        self.assertEqual(text.count(mid1), 1)

    def test_force_appends_duplicate(self):
        body = "force duplicate body"
        mid1 = db.append_message("grok-to-chatgpt", "grok", "chatgpt", body)
        mid2 = db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", body, force=True
        )
        self.assertNotEqual(mid1, mid2)
        text = (self.msg_dir / "grok-to-chatgpt.md").read_text(encoding="utf-8")
        self.assertIn(mid1, text)
        self.assertIn(mid2, text)

    def test_status_counts(self):
        db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "a", status="done"
        )
        db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "b", status="open"
        )
        db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "c", status="blocked"
        )
        db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "d", status="queued"
        )
        st = db.channel_status("grok-to-chatgpt")
        self.assertEqual(st["total"], 4)
        self.assertEqual(st["open"], 1)
        self.assertEqual(st["done"], 1)
        self.assertEqual(st["blocked"], 1)
        self.assertEqual(st["queued"], 1)
        self.assertTrue(st["latest_id"])
        self.assertIn("grok-to-chatgpt.md", st["path"])

    def test_stale_open_ids(self):
        mid = db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "stale candidate", status="open"
        )
        path = self.msg_dir / "grok-to-chatgpt.md"
        text = path.read_text(encoding="utf-8")
        old = (db.now_tr() - dt.timedelta(hours=48)).isoformat(timespec="seconds")
        text2 = re.sub(
            rf"(id: {re.escape(mid)}.*?created_at: )[^\n]+",
            rf"\g<1>{old}",
            text,
            count=1,
            flags=re.S,
        )
        path.write_text(text2, encoding="utf-8")
        stale = db.stale_open_ids("grok-to-chatgpt", older_than_hours=24)
        self.assertEqual(stale, [mid])
        fresh = db.stale_open_ids("grok-to-chatgpt", older_than_hours=100)
        self.assertEqual(fresh, [])

    def test_health_reports_open(self):
        db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "open health", status="open"
        )
        health = db.channel_health("grok-to-chatgpt")
        self.assertIn("channels", health)
        ch = health["channels"]["grok-to-chatgpt"]
        self.assertEqual(ch["open"], 1)
        self.assertIn("problems", health)
        self.assertEqual(set(health["channels"].keys()), {"grok-to-chatgpt"})

    def test_backlog_rows_and_summary(self):
        mid_a = db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "backlog a", status="open"
        )
        mid_b = db.append_message(
            "chatgpt-to-grok", "chatgpt", "grok", "backlog b", status="open"
        )
        db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "done skip", status="done"
        )
        path_a = self.msg_dir / "grok-to-chatgpt.md"
        text_a = path_a.read_text(encoding="utf-8")
        old = (db.now_tr() - dt.timedelta(hours=5)).isoformat(timespec="seconds")
        text_a2 = re.sub(
            rf"(id: {re.escape(mid_a)}.*?created_at: )[^\n]+",
            rf"\g<1>{old}",
            text_a,
            count=1,
            flags=re.S,
        )
        path_a.write_text(text_a2, encoding="utf-8")

        rows = db.open_backlog_rows()
        ids = {r["id"] for r in rows}
        self.assertIn(mid_a, ids)
        self.assertIn(mid_b, ids)
        self.assertEqual(len(rows), 2)
        row_a = next(r for r in rows if r["id"] == mid_a)
        self.assertEqual(row_a["channel"], "grok-to-chatgpt")
        self.assertAlmostEqual(row_a["age_hours"], 5.0, delta=0.2)

        formatted = db.format_backlog()
        self.assertIn(mid_a, formatted)
        self.assertIn("total_open=2", formatted)
        self.assertIn("oldest_open_age_hours=", formatted)

        only = db.open_backlog_rows("chatgpt-to-grok")
        self.assertEqual([r["id"] for r in only], [mid_b])
        self.assertIn("total_open=1", db.format_backlog("chatgpt-to-grok"))

    def test_health_summary_total_open(self):
        mid = db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "health open", status="open"
        )
        path = self.msg_dir / "grok-to-chatgpt.md"
        text = path.read_text(encoding="utf-8")
        old = (db.now_tr() - dt.timedelta(hours=3)).isoformat(timespec="seconds")
        text2 = re.sub(
            rf"(id: {re.escape(mid)}.*?created_at: )[^\n]+",
            rf"\g<1>{old}",
            text,
            count=1,
            flags=re.S,
        )
        path.write_text(text2, encoding="utf-8")
        health = db.channel_health()
        self.assertEqual(health["total_open"], 1)
        self.assertIsInstance(health["oldest_open_age_hours"], float)
        self.assertAlmostEqual(health["oldest_open_age_hours"], 3.0, delta=0.2)
        single = db.channel_health("grok-to-chatgpt")
        self.assertEqual(single["total_open"], 1)
        empty = db.channel_health("inbox-gemini")
        self.assertEqual(empty["total_open"], 0)
        self.assertIsNone(empty["oldest_open_age_hours"])




    def test_inbox_unread_after_write_empty_after_mark(self):
        mid = db.append_message(
            "chatgpt-to-grok", "chatgpt", "grok", "inbox ping", status="open"
        )
        rows = db.unread_message_rows("chatgpt-to-grok")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], mid)
        formatted = db.format_inbox("chatgpt-to-grok")
        self.assertIn(mid, formatted)
        self.assertIn("unread_total=1", formatted)
        db.mark_inbox_read("chatgpt-to-grok")
        rows2 = db.unread_message_rows("chatgpt-to-grok")
        self.assertEqual(rows2, [])
        self.assertIn("unread_total=0", db.format_inbox("chatgpt-to-grok"))
        state = db.load_inbox_read_state()
        self.assertEqual(state["chatgpt-to-grok"]["last_read_id"], mid)

    def test_health_red_when_inbox_unread_older_than_10_min(self):
        mid = db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "stale unread", status="open"
        )
        path = self.msg_dir / "grok-to-chatgpt.md"
        text = path.read_text(encoding="utf-8")
        old = (db.now_tr() - dt.timedelta(minutes=15)).isoformat(timespec="seconds")
        text2 = re.sub(
            rf"(id: {re.escape(mid)}.*?created_at: )[^\n]+",
            rf"\g<1>{old}",
            text,
            count=1,
            flags=re.S,
        )
        path.write_text(text2, encoding="utf-8")
        health = db.channel_health("grok-to-chatgpt")
        ch = health["channels"]["grok-to-chatgpt"]
        self.assertIn("inbox_watch", ch)
        self.assertEqual(ch["inbox_watch"]["unread_count"], 1)
        self.assertGreaterEqual(ch["inbox_watch"]["unread_age_minutes"], 10)
        self.assertFalse(health["healthy"])
        self.assertTrue(
            any(p.startswith("inbox_unread:grok-to-chatgpt:") for p in health["problems"])
        )

    def test_health_green_after_mark_inbox_read(self):
        mid = db.append_message(
            "chatgpt-to-grok", "chatgpt", "grok", "will mark", status="open"
        )
        path = self.msg_dir / "chatgpt-to-grok.md"
        text = path.read_text(encoding="utf-8")
        old = (db.now_tr() - dt.timedelta(minutes=20)).isoformat(timespec="seconds")
        text2 = re.sub(
            rf"(id: {re.escape(mid)}.*?created_at: )[^\n]+",
            rf"\g<1>{old}",
            text,
            count=1,
            flags=re.S,
        )
        path.write_text(text2, encoding="utf-8")
        red = db.channel_health("chatgpt-to-grok")
        self.assertFalse(red["healthy"])
        db.mark_inbox_read("chatgpt-to-grok")
        green = db.channel_health("chatgpt-to-grok")
        watch = green["channels"]["chatgpt-to-grok"]["inbox_watch"]
        self.assertEqual(watch["unread_count"], 0)
        self.assertIsNone(watch["unread_age_minutes"])
        self.assertFalse(
            any(p.startswith("inbox_unread:") for p in green["problems"])
        )
        self.assertTrue(green["healthy"])

    def test_format_inbox_cli_path_via_functions(self):
        db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "cli path a", status="open"
        )
        db.append_message(
            "chatgpt-to-grok", "chatgpt", "grok", "cli path b", status="open"
        )
        out = db.format_inbox()
        self.assertIn("unread_total=2", out)
        self.assertIn("last_write=", out)
        self.assertIn("last_read=", out)
        self.assertIn("unread_age_min=", out)
        db.mark_inbox_read()
        out2 = db.format_inbox()
        self.assertIn("unread_total=0", out2)


    def test_delivery_pending_seen_answered(self):
        mid = db.append_message(
            "chatgpt-to-grok", "chatgpt", "grok", "notify me", status="open"
        )
        st = db.load_delivery_state()["messages"][mid]
        self.assertEqual(st["status"], "pending")
        self.assertTrue(st["alerted"])
        again = db.mark_delivery("chatgpt-to-grok", mid, "pending")
        self.assertEqual(again["status"], "pending")
        db.mark_inbox_read("chatgpt-to-grok")
        self.assertEqual(db.load_delivery_state()["messages"][mid]["status"], "seen")
        reply = db.append_message(
            "grok-to-chatgpt",
            "grok",
            "chatgpt",
            "reply body",
            status="open",
            in_reply_to=mid,
        )
        msgs = db.load_delivery_state()["messages"]
        self.assertEqual(msgs[mid]["status"], "answered")
        self.assertEqual(msgs[reply]["status"], "pending")

    def test_delivery_delayed_and_health(self):
        mid = db.append_message(
            "grok-to-chatgpt", "grok", "chatgpt", "aging ask", status="open"
        )
        state = db.load_delivery_state()
        old = (db.now_tr() - dt.timedelta(minutes=45)).isoformat(timespec="seconds")
        state["messages"][mid]["pending_at"] = old
        state["messages"][mid]["updated_at"] = old
        db.save_delivery_state(state)
        delayed = db.refresh_delayed(older_than_minutes=30)
        self.assertIn(mid, delayed)
        self.assertEqual(db.load_delivery_state()["messages"][mid]["status"], "delayed")
        health = db.channel_health("grok-to-chatgpt")
        self.assertIn("delivery", health)
        self.assertTrue(any(p.startswith("delivery_delayed:") for p in health["problems"]))
        self.assertFalse(health["healthy"])

    def test_format_delivery(self):
        db.append_message(
            "chatgpt-to-grok", "chatgpt", "grok", "fmt delivery", status="open"
        )
        text = db.format_delivery()
        self.assertIn("pending=", text)
        self.assertIn("delivery_total=", text)


if __name__ == "__main__":
    unittest.main()

