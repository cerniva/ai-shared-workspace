import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts import handoff as h

ROOT = Path(__file__).resolve().parents[1]
T0 = "2026-10-09T20:00:00+00:00"


class HandoffTests(unittest.TestCase):
    def new(self):
        data = {"schema_version": 1, "items": []}
        h.add(data, item_id="HO-1", sender="chatgpt", receiver="grok", task="t", reason="r", evidence="e", at=T0)
        return data

    def test_full_lifecycle_and_roles(self):
        data = self.new()
        with self.assertRaises(h.HandoffError):
            h.transition(data, "HO-1", "claim", actor="chatgpt")
        h.transition(data, "HO-1", "claim", actor="grok")
        with self.assertRaises(h.HandoffError):
            h.transition(data, "HO-1", "done", actor="grok", sha="not-a-sha")
        h.transition(data, "HO-1", "done", actor="grok", sha="007431e5223256f9")
        with self.assertRaises(h.HandoffError):
            h.transition(data, "HO-1", "merge", actor="grok")
        item = h.transition(data, "HO-1", "merge", actor="chatgpt", note="verified on main")
        self.assertEqual(item["status"], "merged")
        self.assertIn("merged_at", item)

    def test_status_cannot_skip(self):
        data = self.new()
        with self.assertRaises(h.HandoffError):
            h.transition(data, "HO-1", "done", actor="grok", sha="abcdef1")

    def test_duplicate_and_bad_actor_rejected(self):
        data = self.new()
        with self.assertRaises(h.HandoffError):
            h.add(data, item_id="HO-1", sender="grok", receiver="chatgpt", task="t", reason="r", evidence="e")
        with self.assertRaises(h.HandoffError):
            h.add(data, item_id="HO-2", sender="grok", receiver="grok", task="t", reason="r", evidence="e")

    def test_overdue_after_two_hours(self):
        data = self.new()
        t0 = datetime.fromisoformat(T0)
        self.assertEqual(h.overdue(data, at=t0 + timedelta(hours=1)), [])
        self.assertEqual([i["id"] for i in h.overdue(data, at=t0 + timedelta(hours=3))], ["HO-1"])

    def test_cli_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoffs.json"
            self.assertEqual(h.main(["--file", str(path), "add", "--id", "HO-9", "--from", "grok", "--to", "chatgpt",
                                     "--task", "t", "--reason", "r", "--evidence", "e"]), 0)
            self.assertEqual(h.main(["--file", str(path), "claim", "HO-9", "--actor", "chatgpt"]), 0)
            self.assertEqual(json.loads(path.read_text())["items"][0]["status"], "claimed")

    def test_repo_state_file_is_valid(self):
        data = h.load(ROOT / "state" / "handoffs.json")
        self.assertGreaterEqual(h.validate(data), 1)


if __name__ == "__main__":
    unittest.main()
