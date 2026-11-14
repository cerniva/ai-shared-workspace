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

    def test_case_and_spacing_only_headline_change_is_not_restaged(self):
        # Same official feed headline with harmless case/spacing changes is
        # not a new source or learning, whether pending or in the ledger.
        original = lambda url: ATOM if "github" in url or "shopify" in url else RSS
        first = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=original)
        self.assertEqual(first["domains"]["finance"]["status"], "staged")
        changed_rss = RSS.replace("FOMC statement", "fomc   STATEMENT")
        changed = lambda url: ATOM if "github" in url or "shopify" in url else changed_rss
        pending = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=changed)
        self.assertEqual(pending["domains"]["finance"]["status"], "already_staged")
        target = self.root / first["domains"]["finance"]["path"]
        doc = json.loads(target.read_text(encoding="utf-8"))
        ledger_path = self.root / "knowledge" / "learning_ledger.json"
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        ledger["learnings"].append(doc["learnings"][0])
        ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
        target.unlink()
        persisted = ga.research_learner(root=self.root, adapter=FakeAdapter(), fetch=changed)
        self.assertEqual(persisted["domains"]["finance"]["status"], "already_in_ledger")

    def test_fed_enforcement_article_id_prevents_restaging_renamed_headline(self):
        # Live 2026-10-26 intake repeated the 16 Oct press release already
        # verified in the ledger on 17 Oct under a differently worded title.
        # Dedup by the exact official release ID, not the generated claim ID.
        article = "https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261016a.htm"
        headline = "Federal Reserve Board announces termination of enforcement actions with Gardner Bancshares, Inc. and Small Business Bank"
        feed = RSS.replace("FOMC statement", headline).replace(
            "https://www.federalreserve.gov/x.htm", article)
        known = json.loads((self.root / "knowledge" / "learning_ledger.json").read_text())
        prior = next(row for row in known["learnings"]
                     if row["learning_id"] == "learn_084a973ea4587745")
        self.assertNotEqual(prior["title"], "Federal Reserve Board press releases RSS: " + headline)
        result = ga.research_learner(
            root=self.root, adapter=FakeAdapter(),
            fetch=lambda url: feed if "federalreserve" in url else ATOM)
        self.assertEqual(result["domains"]["finance"]["status"], "already_in_ledger")
        self.assertFalse(list((self.root / "intake" / "promotions").glob(
            "*-research-learner-finance.json")))

        # A genuinely different official release ID must still be stageable.
        unseen = feed.replace("enforcement20261016a", "enforcement20261017b").replace(
            headline, "Federal Reserve Board announces an unrelated new enforcement action")
        second = ga.research_learner(
            root=self.root, adapter=FakeAdapter(),
            fetch=lambda url: unseen if "federalreserve" in url else ATOM)
        self.assertEqual(second["domains"]["finance"]["status"], "staged")

    def test_fed_release_id_rejects_untrusted_or_noncanonical_links(self):
        good = "https://www.federalreserve.gov/newsevents/pressreleases/enforcement20261016a.htm"
        self.assertEqual(ga._fed_enforcement_release_id({"link": good}), "enforcement20261016a")
        for link in (good.replace("https:", "http:"), good + "?utm_source=feed",
                     good + "#fragment", good.replace("www.federalreserve.gov", "evil.example"),
                     good.replace(".htm", ".pdf"), "https://www.federalreserve.gov.evil.example" +
                     "/newsevents/pressreleases/enforcement20261016a.htm"):
            with self.subTest(link=link):
                self.assertIsNone(ga._fed_enforcement_release_id({"link": link}))

    def test_missing_or_malformed_ledger_blocks_staging_without_model_call(self):
        fetch = lambda u: ATOM if "github" in u or "shopify" in u else RSS

        class NoModelCalls:
            def run(self, job):
                raise AssertionError("model must not run when canonical ledger is unavailable")

        ledger_path = self.root / "knowledge" / "learning_ledger.json"
        original = ledger_path.read_bytes()
        for bad in (None, "{broken", "[]", '{"learnings":{}}',
                    '{"learnings":[null]}', '{"learnings":[],"learnings":[]}',
                    '{"learnings":[],"other":NaN}', '{"learnings":[]}',
                    '{"schema_version":true,"learnings":[]}',
                    '{"schema_version":1,"learnings":[{}]}',
                    '{"schema_version":1,"learnings":[{"learning_id":"learn_x","title":"x","source_ids":[]}]}'):
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

    def test_missing_catalog_or_orphan_source_reference_blocks_research(self):
        fetch = lambda u: ATOM if "github" in u or "shopify" in u else RSS

        class NoModelCalls:
            def run(self, job):
                raise AssertionError("model must not run with unverified canonical sources")

        catalog_path = self.root / "knowledge" / "source_catalog.json"
        ledger_path = self.root / "knowledge" / "learning_ledger.json"
        original_catalog, original_ledger = catalog_path.read_bytes(), ledger_path.read_bytes()
        for fault in ("missing_catalog", "malformed_catalog", "duplicate_catalog_id",
                      "orphan_learning_reference"):
            with self.subTest(fault=fault):
                catalog_path.write_bytes(original_catalog)
                ledger_path.write_bytes(original_ledger)
                if fault == "missing_catalog":
                    catalog_path.unlink()
                elif fault == "malformed_catalog":
                    catalog_path.write_text('{"schema_version":true,"sources":[]}')
                elif fault == "duplicate_catalog_id":
                    doc = json.loads(original_catalog)
                    doc["sources"].append(dict(doc["sources"][0]))
                    catalog_path.write_text(json.dumps(doc))
                else:
                    doc = json.loads(original_ledger)
                    doc["learnings"][0]["source_ids"] = ["src_nonexistent_orphan"]
                    ledger_path.write_text(json.dumps(doc))
                result = ga.research_learner(root=self.root, adapter=NoModelCalls(), fetch=fetch)
                self.assertTrue(all(v["status"] == "ledger_unavailable"
                                    for v in result["domains"].values()), result)
                self.assertFalse((self.root / "intake").exists())
        catalog_path.write_bytes(original_catalog)
        ledger_path.write_bytes(original_ledger)

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
                      "extra_source", "extra_learning", "duplicate_source", "duplicate_learning",
                      "schema_bool", "schema_float", "schema_string"):
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
                elif fault == "schema_bool":
                    doc["schema_version"] = True
                elif fault == "schema_float":
                    doc["schema_version"] = 1.0
                elif fault == "schema_string":
                    doc["schema_version"] = "1"
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
    def test_ci_first_page_is_not_global_green(self):
        class PagedHTTP:
            def __call__(self, method, url, body):
                return {"total_count": 2500, "workflow_runs": [
                    {"name": "healthy", "status": "completed", "conclusion": "success"}
                    for _ in range(30)]}

        line = ga._ci_line(ga.GitHub("o/r", "t", PagedHTTP()))
        self.assertIn("KISMİ", line)
        self.assertIn("ilk 30 / 2500", line)
        self.assertIn("tüm CI yeşil doğrulanmadı", line)
        self.assertIn("örnekte başarısız: yok", line)

    def test_ci_distinct_workflows_with_same_display_name_are_not_collapsed(self):
        class SameNameHTTP:
            def __call__(self, method, url, body):
                return {"total_count": 3, "workflow_runs": [
                    {"workflow_id": 101, "name": "CI", "status": "completed", "conclusion": "success"},
                    {"workflow_id": 202, "name": "CI", "status": "completed", "conclusion": "failure"},
                    {"workflow_id": 101, "name": "CI", "status": "completed", "conclusion": "failure"},
                ]}

        line = ga._ci_line(ga.GitHub("o/r", "t", SameNameHTTP()))
        self.assertIn("2 workflow", line)
        self.assertIn("örnekte başarısız: CI#202", line)
        self.assertNotIn("örnekte başarısız: yok", line)
        self.assertNotIn("CI#101", line)

    def test_ci_newest_in_progress_cannot_be_masked_by_old_success(self):
        class PagedHTTP:
            def __call__(self, method, url, body):
                return {"total_count": 3, "workflow_runs": [
                    {"name": "worker", "status": "in_progress", "conclusion": None},
                    {"name": "worker", "status": "completed", "conclusion": "success"},
                    {"name": "codeql", "status": "completed", "conclusion": "success"},
                ]}

        line = ga._ci_line(ga.GitHub("o/r", "t", PagedHTTP()))
        self.assertIn("tam tarama; CI tamamlanmadı", line)
        self.assertIn("örnekte bekleyen: worker", line)
        self.assertIn("örnekte başarısız: yok", line)

    def test_ci_queued_latest_stays_partial_on_paginated_scan(self):
        class PagedHTTP:
            def __call__(self, method, url, body):
                return {"total_count": 31, "workflow_runs": [
                    {"name": "worker", "status": "queued", "conclusion": None},
                    {"name": "worker", "status": "completed", "conclusion": "success"},
                ]}

        line = ga._ci_line(ga.GitHub("o/r", "t", PagedHTTP()))
        self.assertIn("KISMİ", line)
        self.assertIn("örnekte bekleyen: worker", line)

    def test_ci_empty_inventory_is_not_reported_as_green(self):
        class EmptyHTTP:
            def __init__(self, payload):
                self.payload = payload

            def __call__(self, method, url, body):
                return self.payload

        for payload in ({"total_count": 0, "workflow_runs": []},
                        {"workflow_runs": []}):
            with self.subTest(payload=payload):
                line = ga._ci_line(ga.GitHub("o/r", "t", EmptyHTTP(payload)))
                self.assertIn("CI kanıtı yok", line)
                self.assertIn("tüm CI yeşil doğrulanmadı", line)
                self.assertNotIn("tam tarama", line)

    def test_ci_complete_page_and_missing_total_count(self):
        class ResultHTTP:
            def __init__(self, payload):
                self.payload = payload

            def __call__(self, method, url, body):
                return self.payload

        rows = [{"name": "worker", "status": "completed", "conclusion": "failure"},
                {"name": "codeql", "status": "completed", "conclusion": "success"}]
        complete = ga._ci_line(ga.GitHub("o/r", "t", ResultHTTP({
            "total_count": 2, "workflow_runs": rows})))
        self.assertIn("tam tarama", complete)
        self.assertIn("örnekte başarısız: worker", complete)
        unknown = ga._ci_line(ga.GitHub("o/r", "t", ResultHTTP({
            "workflow_runs": rows})))
        self.assertIn("KISMİ", unknown)
        self.assertIn("toplam bilinmiyor", unknown)
        malformed = ga._ci_line(ga.GitHub("o/r", "t", ResultHTTP({
            "total_count": 0, "workflow_runs": None})))
        self.assertIn("workflow_runs eksik", malformed)

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
                                "source_ids": [sid], "plan_tags": ["finance"]}]}
        target.write_text(json.dumps(valid))
        report = ga.reporter(root=self.root, gh=gh,
                             now=datetime(2026, 10, 24, 12, 1, tzinfo=timezone.utc))
        self.assertIn("finance: staged → " + rel, report)
        self.assertEqual(json.loads((self.root / "state" / "agents_history.json").read_text())[-1]["staged"], 1)

        bad_docs = [
            '{broken json',
            # A valid ID alone cannot count as a staged learning for the wrong
            # plan, an inactive learning, or a row without an explicit plan tag.
            json.dumps({**valid, "learnings": [{**valid["learnings"][0],
                                               "plan_tags": ["system"]}]}),
            json.dumps({**valid, "learnings": [{**valid["learnings"][0],
                                               "status": "inactive"}]}),
            json.dumps({**valid, "learnings": [{**valid["learnings"][0],
                                               "plan_tags": []}]}),
            json.dumps({**valid, "learnings": [{k: v for k, v in valid["learnings"][0].items()
                                               if k != "plan_tags"}]}),
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
                          "title": "Injected", "source_ids": [sid], "plan_tags": ["finance"]}]}),
            json.dumps({**valid, "learnings": valid["learnings"] + valid["learnings"]}),
            json.dumps({**valid, "learnings": [{**valid["learnings"][0],
                                               "source_ids": [sid, sid]}]}),
            json.dumps(valid).replace('"schema_version": 1',
                                      '"schema_version": 0, "schema_version": 1', 1),
            json.dumps(valid).replace('"source_id": "' + sid + '"',
                                      '"source_id": "src_fake", "source_id": "' + sid + '"', 1),
            json.dumps(valid).replace('"schema_version": 1',
                                      '"schema_version": 1, "extra": NaN', 1),
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

        # The staging directory itself may be a symlink. Resolving both the
        # target and the boundary would otherwise accept an out-of-scope file.
        target.unlink()
        target.parent.rmdir()
        external_dir = self.root / "outside-promotions"
        external_dir.mkdir()
        (external_dir / target.name).write_text(json.dumps(valid))
        target.parent.symlink_to(external_dir, target_is_directory=True)
        report = ga.reporter(root=self.root, gh=gh,
                             now=datetime(2026, 10, 24, 12, 4, tzinfo=timezone.utc))
        self.assertIn("finance: staged_missing", report)
        self.assertEqual(json.loads((self.root / "state" / "agents_history.json").read_text())[-1]["staged"], 0)

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
                              "claim": claim, "title": "Verified staged candidate", "source_ids": [sid], "plan_tags": ["finance"]}]}
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

    def test_reporter_requires_canonical_source_catalog_for_staged_claim(self):
        canonical = "https://www.federalreserve.gov/feeds/press_all.xml"
        domain, claim = "finance-news", "Catalog unavailable."
        sid = ga.source_id(ga.canonicalize(canonical))
        lid = ga.learning_id(domain, claim)
        rel = "intake/promotions/2026-10-25-research-learner-finance.json"
        target = self.root / rel
        target.parent.mkdir(parents=True)
        target.write_text(json.dumps({
            "schema_version": 1,
            "sources": [{"source_id": sid, "canonical": canonical}],
            "learnings": [{"learning_id": lid, "domain": domain,
                           "claim": claim, "title": "Verified staged candidate", "source_ids": [sid], "plan_tags": ["finance"]}]}))
        (self.root / "state" / "research_learner.json").write_text(json.dumps({
            "domains": {"finance": {"status": "staged", "path": rel,
                                    "source_id": sid, "learning_id": lid}}}))
        (self.root / "knowledge" / "source_catalog.json").unlink()
        report = ga.reporter(root=self.root, gh=ga.GitHub("o/r", "t", FakeHTTP()),
                             now=datetime(2026, 10, 25, 21, 0, tzinfo=timezone.utc))
        self.assertIn("finance: staged_unverified (canonical ledger unavailable)", report)
        self.assertEqual(json.loads((self.root / "state" / "agents_history.json").read_text())[-1]["staged"], 0)

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
                           "claim": claim, "title": "Verified staged candidate", "source_ids": [sid], "plan_tags": ["finance"]}]}))
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
                           "claim": claim, "title": "Verified staged candidate", "source_ids": [sid], "plan_tags": ["finance"]}]
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


class StrictResearchJSONTests(unittest.TestCase):
    def test_dedup_does_not_follow_symlinked_intake_parent(self):
        canonical = "https://www.federalreserve.gov/feeds/press_all.xml"
        sid = ga.source_id(ga.canonicalize(canonical))
        domain, claim = "research-staging", "Dedup must stay inside the repository."
        lid = ga.learning_id(domain, claim)
        title = "Outside candidate must not suppress new research"
        doc = {"schema_version": 1,
               "sources": [{"source_id": sid, "canonical": canonical}],
               "learnings": [{"learning_id": lid, "domain": domain, "claim": claim,
                              "title": title, "source_ids": [sid]}]}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            inside = root / "intake" / "promotions"
            inside.mkdir(parents=True)
            (inside / "candidate.json").write_text(json.dumps(doc), encoding="utf-8")
            self.assertEqual(ga._staged_learning_titles(root), {title})

            (inside / "candidate.json").unlink()
            inside.rmdir()
            (root / "intake").rmdir()
            external = Path(temp) / "external"
            (external / "promotions").mkdir(parents=True)
            (external / "promotions" / "candidate.json").write_text(
                json.dumps(doc), encoding="utf-8")
            (root / "intake").symlink_to(external, target_is_directory=True)
            self.assertEqual(ga._staged_learning_titles(root), set())

    def test_canonical_ledger_schema_and_identities_fail_closed(self):
        canonical = json.loads((ROOT / "knowledge" / "learning_ledger.json").read_text(encoding="utf-8"))
        self.assertEqual(len(ga._canonical_learning_rows(canonical)), len(canonical["learnings"]))
        row = dict(canonical["learnings"][0])
        for bad in (
            {"learnings": canonical["learnings"]},
            {"schema_version": True, "learnings": canonical["learnings"]},
            {"schema_version": 1, "learnings": [dict(row, title="")]},
            {"schema_version": 1, "learnings": [dict(row, domain="tampered-domain")]},
            {"schema_version": 1, "learnings": [dict(row, claim="tampered claim")]},
            {"schema_version": 1, "learnings": [dict(row, source_ids=[])]},
            {"schema_version": 1, "learnings": [row, dict(row)]},
        ):
            with self.subTest(bad=str(bad)[:80]):
                self.assertIsNone(ga._canonical_learning_rows(bad))

    def test_canonical_source_identity_and_normalized_url_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "knowledge").mkdir()
            catalog = json.loads((ROOT / "knowledge" / "source_catalog.json").read_text(encoding="utf-8"))
            target = root / "knowledge" / "source_catalog.json"
            target.write_text(json.dumps(catalog), encoding="utf-8")
            self.assertEqual(len(ga._canonical_source_ids(root)), len(catalog["sources"]))
            row = catalog["sources"][0]
            for bad in (
                dict(row, source_id="src_forged"),
                dict(row, canonical=row["canonical"].replace("https://", "HTTPS://", 1)),
            ):
                with self.subTest(bad=bad):
                    modified = {**catalog, "sources": [bad, *catalog["sources"][1:]]}
                    target.write_text(json.dumps(modified), encoding="utf-8")
                    self.assertIsNone(ga._canonical_source_ids(root))

    def test_staged_source_url_must_be_canonical_before_readback(self):
        canonical = "https://www.federalreserve.gov/feeds/press_all.xml"
        sid = ga.source_id(ga.canonicalize(canonical))
        domain, claim = "research-canonical-gate", "Reject noncanonical staged source URLs."
        lid = ga.learning_id(domain, claim)
        doc = {
            "schema_version": 1,
            "sources": [{"source_id": sid, "canonical": canonical}],
            "learnings": [{"learning_id": lid, "domain": domain, "claim": claim,
                           "title": "Staged URL normalization gate", "source_ids": [sid]}],
        }
        self.assertIsNotNone(ga._validated_staged_rows(doc))
        doc["sources"][0]["canonical"] = canonical.replace("https://", "HTTPS://", 1)
        self.assertIsNone(ga._validated_staged_rows(doc))

    def test_duplicate_keys_and_nonfinite_values_fail_closed(self):
        for raw in ('{"x":1,"x":2}', '{"nested":{"x":1,"x":2}}',
                    '{"x":NaN}', '{"x":Infinity}', '{"x":-Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                ga._strict_json_loads(raw)
        self.assertEqual(ga._strict_json_loads('{"ok":[{"x":1}]}'),
                         {"ok": [{"x": 1}]})


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
