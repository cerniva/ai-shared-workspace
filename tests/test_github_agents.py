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

    def test_headline_already_in_ledger_is_not_restaged(self):
        fetch = lambda u: ATOM if "github" in u or "shopify" in u else RSS
        first = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=fetch)
        ledger_path = self.root / "knowledge" / "learning_ledger.json"
        ledger = json.loads(ledger_path.read_text())
        for v in first["domains"].values():
            if v["status"] == "staged":
                doc = json.loads((self.root / v["path"]).read_text())
                ledger["learnings"].append(doc["learnings"][0])
                (self.root / v["path"]).unlink()
        ledger_path.write_text(json.dumps(ledger))
        again = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=fetch)
        self.assertTrue(all(v["status"] == "already_in_ledger" for v in again["domains"].values()), again)

    def test_missing_or_malformed_ledger_blocks_staging_without_model_call(self):
        fetch = lambda u: ATOM if "github" in u or "shopify" in u else RSS

        class NoModelCalls:
            def run(self, job):
                raise AssertionError("model must not run when canonical ledger is unavailable")

        ledger_path = self.root / "knowledge" / "learning_ledger.json"
        original = ledger_path.read_bytes()
        for bad in (None, "{broken", "[]", '{"learnings":{}}',
                    '{"learnings":[null]}'):
            with self.subTest(bad=bad):
                if bad is None:
                    ledger_path.unlink(missing_ok=True)
                else:
                    ledger_path.write_text(bad, encoding="utf-8")
                result = ga.research_learner(root=self.root, adapter=NoModelCalls(), fetch=fetch)
                self.assertEqual(set(result["domains"]), set(ga.RESEARCH_SOURCES))
                self.assertTrue(all(v["status"] == "ledger_unavailable"
                                    for v in result["domains"].values()), result)
                self.assertFalse((self.root / "intake").exists())
                saved = json.loads((self.root / "state" / "research_learner.json").read_text())
                self.assertEqual(saved["domains"], result["domains"])
        ledger_path.write_bytes(original)

    def test_pending_intake_dedup_preserves_existing_bytes(self):
        fetch = lambda u: ATOM if "github" in u or "shopify" in u else RSS
        first = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=fetch)
        saved = {v["path"]: (self.root / v["path"]).read_bytes()
                 for v in first["domains"].values() if v["status"] == "staged"}
        self.assertEqual(len(saved), 3)
        again = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=fetch)
        self.assertTrue(all(v["status"] == "already_staged"
                            for v in again["domains"].values()), again)
        self.assertEqual(saved, {p: (self.root / p).read_bytes() for p in saved})

    def test_invalid_pending_identity_does_not_mask_new_research(self):
        fetch = lambda u: ATOM if "github" in u or "shopify" in u else RSS
        first = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=fetch)
        target = self.root / first["domains"]["finance"]["path"]
        original = json.loads(target.read_text(encoding="utf-8"))
        for fault in ("source_refs", "source_identity", "learning_identity",
                      "extra_source", "extra_learning", "duplicate_source", "duplicate_learning"):
            with self.subTest(fault=fault):
                doc = json.loads(json.dumps(original))
                if fault == "source_refs":
                    doc["learnings"][0]["source_ids"] = ["src_nonexistent"]
                elif fault == "source_identity":
                    doc["sources"][0]["source_id"] = "src_wrong"
                    doc["learnings"][0]["source_ids"] = ["src_wrong"]
                elif fault == "learning_identity":
                    doc["learnings"][0]["learning_id"] = "learn_wrong"
                elif fault == "extra_source":
                    doc["sources"].append({"source_id": "src_fake", "canonical": "https://example.org/bad"})
                elif fault == "extra_learning":
                    doc["learnings"].append({"learning_id": "learn_fake", "domain": "finance-news",
                                              "claim": "invalid", "title": "Injected", "source_ids":
                                              [doc["sources"][0]["source_id"]]})
                elif fault == "duplicate_source":
                    doc["sources"].append(dict(doc["sources"][0]))
                elif fault == "duplicate_learning":
                    doc["learnings"].append(dict(doc["learnings"][0]))
                target.write_text(json.dumps(doc), encoding="utf-8")
                second = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=fetch)
                self.assertEqual(second["domains"]["finance"]["status"], "staging_collision", second)
                self.assertEqual(json.loads(target.read_text(encoding="utf-8")), doc)
                self.assertEqual(second["domains"]["video_shopify"]["status"], "already_staged")

    def test_new_headline_same_day_never_overwrites_pending_candidate(self):
        fetch = lambda u: ATOM if "github" in u or "shopify" in u else RSS
        first = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=fetch)
        saved = {v["path"]: (self.root / v["path"]).read_bytes()
                 for v in first["domains"].values() if v["status"] == "staged"}
        changed = lambda u: (ATOM.replace("New API", "Another API")
                             if "github" in u or "shopify" in u
                             else RSS.replace("FOMC statement", "FOMC update"))
        again = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=changed)
        self.assertTrue(all(v["status"] == "staging_collision"
                            for v in again["domains"].values()), again)
        self.assertEqual(saved, {p: (self.root / p).read_bytes() for p in saved})

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


    def test_staged_candidate_requires_live_intake_readback(self):
        rel = "intake/promotions/2026-10-24-research-learner-finance.json"
        canonical = "https://www.federalreserve.gov/feeds/press_all.xml"
        domain, claim = "finance-news", "Research staging must preserve provenance."
        sid = ga.source_id(ga.canonicalize(canonical))
        lid = ga.learning_id(domain, claim)
        (self.root / "state" / "research_learner.json").write_text(json.dumps({
            "domains": {"finance": {"status": "staged", "path": rel,
                                    "source_id": sid, "learning_id": lid}}
        }))
        gh = ga.GitHub("o/r", "t", FakeHTTP())
        report = ga.reporter(root=self.root, gh=gh,
                             now=datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc))
        self.assertIn("finance: staged_missing", report)
        self.assertEqual(json.loads((self.root / "state" / "agents_history.json").read_text())[-1]["staged"], 0)

        target = self.root / rel
        target.parent.mkdir(parents=True)
        valid = {"schema_version": 1, "sources": [{"source_id": sid, "canonical": canonical}],
                 "learnings": [{"learning_id": lid, "domain": domain, "claim": claim, "title": "Verified staged candidate",
                                "source_ids": [sid]}]}
        target.write_text(json.dumps(valid))
        report = ga.reporter(root=self.root, gh=gh,
                             now=datetime(2026, 10, 24, 12, 1, tzinfo=timezone.utc))
        self.assertIn("finance: staged → " + rel, report)
        self.assertEqual(json.loads((self.root / "state" / "agents_history.json").read_text())[-1]["staged"], 1)

        bad_docs = [
            '{broken json',
            json.dumps({**valid, "schema_version": 0}),
            json.dumps({**valid, "learnings": [{**valid["learnings"][0], "source_ids": ["wrong"]}]}),
            json.dumps({**valid, "sources": [{**valid["sources"][0],
                                             "canonical": "https://example.org/changed"}]}),
            json.dumps({**valid, "learnings": [{**valid["learnings"][0],
                                               "claim": "tampered claim"}]}),
            json.dumps({**valid, "sources": valid["sources"] +
                        [{"source_id": "src_fake", "canonical": "https://example.org/bad"}]}),
            json.dumps({**valid, "sources": valid["sources"] + valid["sources"]}),
            json.dumps({**valid, "learnings": valid["learnings"] +
                        [{"learning_id": "learn_fake", "domain": domain, "claim": "bad",
                          "title": "Injected", "source_ids": [sid]}]}),
            json.dumps({**valid, "learnings": valid["learnings"] + valid["learnings"]}),
            json.dumps({**valid, "learnings": [{**valid["learnings"][0],
                                               "source_ids": [sid, sid]}]}),
        ]
        for bad in bad_docs:
            target.write_text(bad)
            report = ga.reporter(root=self.root, gh=gh,
                                 now=datetime(2026, 10, 24, 12, 2, tzinfo=timezone.utc))
            self.assertIn("finance: staged_missing", report)
            self.assertEqual(json.loads((self.root / "state" / "agents_history.json").read_text())[-1]["staged"], 0)

        target.unlink()
        outside = self.root / "outside.json"
        outside.write_text(json.dumps(valid))
        target.symlink_to(outside)
        report = ga.reporter(root=self.root, gh=gh,
                             now=datetime(2026, 10, 24, 12, 3, tzinfo=timezone.utc))
        self.assertIn("finance: staged_missing", report)

    def test_already_promoted_intake_is_not_counted_as_new(self):
        rel = "intake/promotions/2026-10-25-research-learner-finance.json"
        canonical = "https://www.federalreserve.gov/feeds/press_all.xml"
        domain, claim = "finance-news", "Previously promoted exact claim."
        sid = ga.source_id(ga.canonicalize(canonical))
        lid = ga.learning_id(domain, claim)
        target = self.root / rel
        target.parent.mkdir(parents=True)
        doc = {"schema_version": 1,
               "sources": [{"source_id": sid, "canonical": canonical}],
               "learnings": [{"learning_id": lid, "domain": domain,
                              "claim": claim, "title": "Verified staged candidate", "source_ids": [sid]}]}
        target.write_text(json.dumps(doc))
        original = target.read_bytes()
        (self.root / "state" / "research_learner.json").write_text(json.dumps({
            "domains": {"finance": {"status": "staged", "path": rel,
                                    "source_id": sid, "learning_id": lid}}}))
        ledger_path = self.root / "knowledge" / "learning_ledger.json"
        ledger = json.loads(ledger_path.read_text())
        ledger["learnings"].append(doc["learnings"][0])
        ledger_path.write_text(json.dumps(ledger))
        report = ga.reporter(root=self.root, gh=ga.GitHub("o/r", "t", FakeHTTP()),
                             now=datetime(2026, 10, 25, 21, 0, tzinfo=timezone.utc))
        self.assertIn("finance: already_in_ledger (staged file retained; not new)", report)
        self.assertNotIn("finance: staged →", report)
        self.assertEqual(json.loads((self.root / "state" / "agents_history.json").read_text())[-1]["staged"], 0)
        self.assertEqual(target.read_bytes(), original)

    def test_unreadable_ledger_never_claims_fresh_staging(self):
        rel = "intake/promotions/2026-10-25-research-learner-finance.json"
        canonical = "https://www.federalreserve.gov/feeds/press_all.xml"
        domain, claim = "finance-news", "Ledger unavailable."
        sid = ga.source_id(ga.canonicalize(canonical))
        lid = ga.learning_id(domain, claim)
        target = self.root / rel
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({
            "schema_version": 1,
            "sources": [{"source_id": sid, "canonical": canonical}],
            "learnings": [{"learning_id": lid, "domain": domain,
                           "claim": claim, "title": "Verified staged candidate", "source_ids": [sid]}]}))
        (self.root / "state" / "research_learner.json").write_text(json.dumps({
            "domains": {"finance": {"status": "staged", "path": rel,
                                    "source_id": sid, "learning_id": lid}}}))
        (self.root / "knowledge" / "learning_ledger.json").write_text("{broken")
        report = ga.reporter(root=self.root, gh=ga.GitHub("o/r", "t", FakeHTTP()),
                             now=datetime(2026, 10, 25, 21, 0, tzinfo=timezone.utc))
        self.assertIn("finance: staged_unverified (canonical ledger unavailable)", report)
        self.assertEqual(json.loads((self.root / "state" / "agents_history.json").read_text())[-1]["staged"], 0)


    def test_unreadable_ledger_checks_each_domain_not_last_candidate(self):
        canonical = "https://www.federalreserve.gov/feeds/press_all.xml"
        domain, claim = "finance-news", "Valid staged learning with unavailable ledger."
        sid = ga.source_id(ga.canonicalize(canonical))
        lid = ga.learning_id(domain, claim)
        rel = "intake/promotions/2026-10-25-research-learner-finance.json"
        target = self.root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "schema_version": 1,
            "sources": [{"source_id": sid, "canonical": canonical}],
            "learnings": [{"learning_id": lid, "domain": domain,
                           "claim": claim, "title": "Verified staged candidate", "source_ids": [sid]}]
        }), encoding="utf-8")
        (self.root / "knowledge" / "learning_ledger.json").write_text(
            "{broken", encoding="utf-8")
        valid = {"status": "staged", "path": rel, "source_id": sid, "learning_id": lid}
        missing = {"status": "staged",
                   "path": "intake/promotions/nonexistent.json",
                   "source_id": sid, "learning_id": lid}
        for order in (("finance", "video_shopify"), ("video_shopify", "finance")):
            with self.subTest(order=order):
                entries = {"finance": valid, "video_shopify": missing}
                (self.root / "state" / "research_learner.json").write_text(
                    json.dumps({"domains": {name: entries[name] for name in order}}),
                    encoding="utf-8")
                report = ga.reporter(root=self.root, gh=ga.GitHub("o/r", "t", FakeHTTP()),
                                     now=datetime(2026, 10, 25, 21, 0,
                                                  tzinfo=timezone.utc))
                self.assertIn("finance: staged_unverified (canonical ledger unavailable)", report)
                self.assertIn("video_shopify: staged_missing", report)
                self.assertNotIn("video_shopify: staged_unverified", report)
                self.assertEqual(json.loads((self.root / "state" / "agents_history.json")
                                            .read_text())[-1]["staged"], 0)


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
