import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from scripts import shorts_lesson_48h as L, youtube_video_metrics as M

T0 = dt.datetime(2026, 10, 10, 0, 0, tzinfo=dt.timezone.utc)
API = {"columnHeaders": [{"name": n} for n in M.METRICS],
       "rows": [[1000, 600, 120.0, 9.0, 55.0, 40, 3, 2, 5]]}


def ok_fetch(video_id, start, end):
    return {"video_id": video_id, "start": start.isoformat(), "end": end.isoformat(),
            "source": "youtube_analytics_api_v2", "status": "COMPLETED", "metrics": M.parse_report(API)}


class Lesson48hTests(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.doc = L.record({"schema": 1, "uploads": []}, "vid1", T0.isoformat(), title="t")

    def test_record_is_idempotent(self):
        L.record(self.doc, "vid1", T0.isoformat())
        self.assertEqual(len(self.doc["uploads"]), 1)

    def test_not_due_before_48h(self):
        self.assertEqual(L.due(self.doc, T0 + dt.timedelta(hours=47)), [])
        self.assertEqual(len(L.due(self.doc, T0 + dt.timedelta(hours=48))), 1)

    def test_run_appends_lesson_and_marks_ledger(self):
        lessons = self.d / "video-lessons.md"
        written = L.run(self.doc, ok_fetch, lessons, T0 + dt.timedelta(hours=49))
        self.assertEqual(written, ["vid1"])
        text = lessons.read_text()
        self.assertIn("vid1 — 48h lesson", text)
        self.assertIn("Average % viewed < 70", text)
        self.assertIn("Likes/1k views >= 30", text)
        self.assertTrue(self.doc["uploads"][0]["lesson_at"])
        self.assertEqual(L.due(self.doc, T0 + dt.timedelta(hours=60)), [])

    def test_blocked_metrics_write_no_lesson_and_stay_due(self):
        lessons = self.d / "video-lessons.md"
        blocked = lambda *a: {"status": "blocked", "reason_code": "insufficient_scope"}
        self.assertEqual(L.run(self.doc, blocked, lessons, T0 + dt.timedelta(hours=49)), [])
        self.assertFalse(lessons.exists())
        e = self.doc["uploads"][0]
        self.assertEqual((e["attempts"], e["last_error"], e["lesson_at"]), (1, "insufficient_scope", None))

    def test_cli_record_and_due(self):
        ledger = self.d / "ledger.json"
        self.assertEqual(L.main(["record", "--video-id", "abc", "--uploaded-at", "2020-01-01T00:00:00Z", "--ledger", str(ledger)]), 0)
        self.assertEqual(json.loads(ledger.read_text())["uploads"][0]["video_id"], "abc")

    def test_repo_ledger_is_valid(self):
        self.assertIsInstance(L.load()["uploads"], list)


class VideoMetricsTests(unittest.TestCase):
    def test_missing_secret_is_blocked_not_fake(self):
        r = M.fetch("v", dt.date(2026, 10, 1), dt.date(2026, 10, 3), env={})
        self.assertEqual(r["reason_code"], "missing-secret")

    def test_query_filters_video(self):
        q = M.build_query("v1", dt.date(2026, 10, 1), dt.date(2026, 10, 3))
        self.assertEqual(q["filters"], "video==v1")
        self.assertIn("engagedViews", q["metrics"]); self.assertIn("likes", q["metrics"])

    def test_parse_and_swipe_not_faked(self):
        m = M.parse_report(API)
        self.assertEqual((m["views"], m["likes"], m["watch_time_hours"]), (1000, 40, 2.0))
        self.assertEqual(m["likes_per_1k_views"], 40.0)
        self.assertIsNone(m["stayed_to_watch_percent"])

    def test_scope_error_reported(self):
        class Boom:
            def reports(self): raise RuntimeError("403 insufficientPermissions: Request had insufficient authentication scopes")
        env = {k: "x" for k in M.SECRETS}
        r = M.fetch("v", dt.date(2026, 10, 1), dt.date(2026, 10, 3), env=env, client_factory=lambda e: Boom())
        self.assertEqual((r["status"], r["reason_code"]), ("blocked", "insufficient_scope"))

    def test_upload_workflow_records_ledger_and_installs_ffprobe(self):
        text = (L.ROOT / ".github/workflows/youtube-upload.yml").read_text()
        self.assertIn("shorts_lesson_48h.py record", text)
        self.assertIn("apt-get install", text); self.assertIn("ffprobe", text)
        lessons = (L.ROOT / ".github/workflows/shorts-48h-lessons.yml").read_text()
        self.assertIn("*/6", lessons); self.assertIn("shorts_lesson_48h.py run", lessons)
        self.assertNotIn("youtube_upload.py", lessons)


if __name__ == "__main__":
    unittest.main()
