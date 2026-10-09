from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import github_agents as ga

ROOT = Path(__file__).resolve().parents[1]
RSS = ("<rss><channel><title>t</title><item><title>FOMC statement</title>"
       "<link>https://www.federalreserve.gov/x.htm</link><pubDate>Wed, 07 Oct 2026 18:00:00 GMT</pubDate>"
       "</item></channel></rss>")
ATOM = ('<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>New API</title>'
        '<link href="https://example.org/a"/><updated>2026-10-09T00:00:00Z</updated></entry></feed>')


class FakeAdapter:
    provider = "fake"

    def run(self, job):
        return {"provider": "deepseek", "recommendation": "Review the item for plan relevance."}


class FakeHTTP:
    def __init__(self):
        self.calls = []

    def __call__(self, method, url, body):
        self.calls.append((method, url, body))
        if method == "POST":
            return {}
        if "/actions/runs?" in url:
            return {"workflow_runs": [{"name": "a", "status": "completed", "conclusion": "failure"}]}
        return {"workflow_runs": [{"id": 42, "status": "completed", "conclusion": "success",
                                   "created_at": "2026-10-10T00:00:00Z", "event": "schedule"}]}


class Base(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "knowledge").mkdir()
        (self.root / "state").mkdir()
        for name in ("source_catalog.json", "learning_ledger.json"):
            shutil.copyfile(ROOT / "knowledge" / name, self.root / "knowledge" / name)
        (self.root / "state" / "handoffs.json").write_text(json.dumps({"schema_version": 1, "items": [
            {"id": "HO-9", "from": "chatgpt", "to": "claude", "task": "t", "reason_cannot_do": "r", "evidence": "e",
             "status": "open", "created_at": "2026-10-09T00:00:00+00:00", "updated_at": "2026-10-09T00:00:00+00:00"}]}))


class AutomationRunnerTests(Base):
    def test_observes_all_four_and_dispatches_only_allowlist(self):
        http = FakeHTTP()
        rep = ga.automation_runner(root=self.root, gh=ga.GitHub("o/r", "t", http), adapter=None)
        self.assertEqual(set(rep["automations"]), {"finance", "video_shorts_shopify_gumroad", "knowledge", "system"})
        posts = [u for m, u, _ in http.calls if m == "POST"]
        self.assertTrue(all(u.endswith(("plan-learnings-check.yml/dispatches", "worker-orchestration-tests.yml/dispatches"))
                            for u in posts))
        self.assertFalse(any("youtube-upload" in u for u in posts))
        self.assertEqual(rep["automations"]["video_shorts_shopify_gumroad"]["mode"], "dry-run")
        self.assertEqual(rep["automations"]["knowledge"]["workflows"]["knowledge-promote.yml"]["id"], 42)
        self.assertIsNone(rep["model_summary"])
        self.assertTrue((self.root / "state" / "automation_runner.json").exists())

    def test_no_token_never_crashes(self):
        rep = ga.automation_runner(root=self.root, gh=ga.GitHub(None, None), adapter=None)
        self.assertFalse(rep["github_api"])

    def test_dispatch_targets_exist_and_are_not_publishers(self):
        for spec in ga.AUTOMATIONS.values():
            for wf in spec["observe"] + spec["dispatch"]:
                self.assertTrue((ROOT / ".github" / "workflows" / wf).exists(), wf)
            for wf in spec["dispatch"]:
                self.assertNotIn("upload", wf)


class ResearchLearnerTests(Base):
    def test_skips_without_provider(self):
        rep = ga.research_learner(root=self.root, adapter=None, fetch=lambda u: RSS)
        self.assertEqual(rep["skipped"], "no provider key")
        self.assertFalse((self.root / "intake").exists())

    def test_stages_valid_promotions_in_intake_only(self):
        rep = ga.research_learner(root=self.root, adapter=FakeAdapter(),
                                  fetch=lambda u: ATOM if "github" in u or "shopify" in u else RSS)
        staged = [v for v in rep["domains"].values() if v["status"] == "staged"]
        self.assertEqual(len(staged), 3)
        for v in staged:
            self.assertTrue(v["path"].startswith("intake/promotions/"))
            doc = json.loads((self.root / v["path"]).read_text())
            self.assertEqual(doc["schema_version"], 1)
            self.assertEqual(doc["learnings"][0]["provenance"], "unverified")
            self.assertEqual(doc["learnings"][0]["source_ids"], [doc["sources"][0]["source_id"]])
        self.assertFalse((self.root / "knowledge" / "promotions").exists())

    def test_fetch_error_recorded(self):
        def boom(url):
            raise OSError("down")
        rep = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=boom)
        self.assertTrue(all(v["status"].startswith("fetch_error") for v in rep["domains"].values()))

    def test_parse_feed(self):
        self.assertEqual(ga.parse_feed(RSS)["title"], "FOMC statement")
        self.assertEqual(ga.parse_feed(ATOM)["link"], "https://example.org/a")
        self.assertIsNone(ga.parse_feed("not xml"))


class ReporterTests(Base):
    def test_writes_both_turkish_files(self):
        text = ga.reporter(root=self.root, gh=ga.GitHub("o/r", "t", FakeHTTP()),
                           now=datetime(2026, 10, 10, 9, 0, tzinfo=timezone.utc))
        for rel in ("messages/agents-report-latest.md", "messages/chatgpt-to-read.md"):
            self.assertEqual((self.root / rel).read_text(encoding="utf-8"), text)
        self.assertIn("Saatlik", text)
        self.assertIn("Günlük", text)
        self.assertIn("HO-9", text)
        self.assertIn("12:00 TRT", text)
        self.assertIn("başarısız: a", text)


class SafetyTests(unittest.TestCase):
    def test_output_paths_restricted(self):
        root = Path("/tmp/x")
        for bad in (".github/workflows/a.yml", "scripts/a.py", "state/../.github/a", "intake/PayoutLens/a.json"):
            with self.assertRaises(ValueError):
                ga.safe_output_path(root, bad)
        ga.safe_output_path(root, "messages/chatgpt-to-read.md")

    def test_workflows(self):
        for name, cron in (("automation-runner", "13 */2 * * *"), ("research-learner", "37 5 * * *"),
                           ("agents-reporter", "47 * * * *")):
            text = (ROOT / ".github" / "workflows" / f"{name}.yml").read_text()
            self.assertIn(f"cron: '{cron}'", text)
            self.assertIn("unexpected staged path", text)
            self.assertIn("actions/checkout@v7", text)
            self.assertNotIn("secrets.XAI_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
