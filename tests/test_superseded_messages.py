import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import scripts.desk_bridge as db

ROOT = Path(__file__).resolve().parents[1]


def block(mid, created, status="open"):
    return f"---\nid: {mid}\nfrom: chatgpt\nto: grok\nin_reply_to: none\ncreated_at: {created}\nproject: workspace\nstatus: {status}\n---\nintent: x | ask\n"


class SupersededMessagesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.chan = base / "chatgpt-to-grok.md"
        self.chan.write_text(block("MSG-old", "2026-10-01T10:00:00+03:00")
                             + block("MSG-new", "2026-10-09T10:00:00+03:00"), encoding="utf-8")
        self.sup = base / "superseded_messages.json"
        self.sup.write_text(json.dumps({"cutoff": "2026-10-09T00:00:00+03:00", "reason": "r", "ids": ["MSG-old"]}),
                            encoding="utf-8")
        self.patches = [
            mock.patch.object(db, "CHANNELS", {"chatgpt-to-grok": (self.chan, "chatgpt", "grok")}),
            mock.patch.object(db, "SUPERSEDED_PATH", self.sup),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.tmp.cleanup()

    def test_open_backlog_and_status_skip_superseded(self):
        self.assertEqual(db.open_message_ids("chatgpt-to-grok"), ["MSG-new"])
        self.assertEqual([r["id"] for r in db.open_backlog_rows()], ["MSG-new"])
        self.assertEqual(db.channel_status("chatgpt-to-grok")["open"], 1)
        self.assertEqual(db.stale_open_ids("chatgpt-to-grok", older_than_hours=0), ["MSG-new"])

    def test_missing_file_means_nothing_superseded(self):
        self.sup.unlink()
        self.assertEqual(db.open_message_ids("chatgpt-to-grok"), ["MSG-old", "MSG-new"])

    def test_repo_file_only_lists_pre_cutoff_ids(self):
        data = json.loads((ROOT / "state" / "superseded_messages.json").read_text(encoding="utf-8"))
        cutoff = db._parse_created_at(data["cutoff"])
        self.assertTrue(data["ids"])
        for mid in data["ids"]:
            stamp = mid.split("-")[1]
            self.assertLess(stamp, cutoff.strftime("%Y%m%d"), mid)


if __name__ == "__main__":
    unittest.main()
