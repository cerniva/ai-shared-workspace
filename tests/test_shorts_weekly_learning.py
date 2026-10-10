import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import shorts_weekly_learning as w  # noqa: E402

GOOD = {"status": "COMPLETED", "run_id": "r1", "result": {
    "channel_name": "Cerno", "period": "Last 28 days", "views": 5300,
    "watch_time_hours": 9.5, "subscribers_change": 6,
    "top_videos": [{"title": "A", "views": 2610}, {"title": "B", "views": 1219}, {"title": "C", "views": 1122}]}}


class T(unittest.TestCase):
    def run_main(self, doc):
        d = Path(tempfile.mkdtemp())
        src = d / "a.json"
        src.write_text(json.dumps(doc))
        code = w.main([str(src), "--out-dir", str(d / "out"), "--date", "2026-10-10"])
        return code, d / "out" / "weekly-2026-41.md"

    def test_writes_note(self):
        code, path = self.run_main(GOOD)
        self.assertEqual(code, 0)
        text = path.read_text()
        self.assertIn("2026-W41", text)
        self.assertIn("49% of channel views", text)
        self.assertIn("6.5 s watched per view", text)

    def test_rejects_dry_run(self):
        code, path = self.run_main({"dry_run": True, "payload": {}})
        self.assertEqual(code, 2)
        self.assertFalse(path.exists())

    def test_rejects_not_completed(self):
        self.assertEqual(self.run_main({"status": "blocked", "reason_code": "missing-secret"})[0], 2)

    def test_rejects_not_signed_in(self):
        doc = {"status": "COMPLETED", "result": {"error": "NOT_SIGNED_IN"}}
        self.assertEqual(self.run_main(doc)[0], 2)

    def test_rejects_missing_views(self):
        doc = {"status": "COMPLETED", "result": {"channel_name": "x", "period": "p"}}
        self.assertEqual(self.run_main(doc)[0], 2)


if __name__ == "__main__":
    unittest.main()
