import json
import re
import tempfile
import unittest
from pathlib import Path

from scripts import lesson_learner as ll

SHA = "abcdef1234567890abcdef1234567890abcdef12"


class FakeGH:
    def __init__(self, files=None, head="feat/x", branches=(), open_heads=()):
        self.posts = []
        self.pr = {"number": 7, "title": "feat: thing HO-20261010-03", "body": "b", "merged": True,
                   "merge_commit_sha": SHA, "base": {"ref": "main"}, "head": {"ref": head}}
        self.files = files or ["scripts/a.py"]
        self.branches, self.open_heads = list(branches), list(open_heads)

    def call(self, method, path, body=None):
        if method == "POST":
            self.posts.append((path, body))
            return {"number": 99, "head": {"sha": "feedbeef"}}
        if path == "/pulls/7":
            return self.pr
        if path.startswith("/pulls/7/files"):
            return [{"filename": f} for f in self.files]
        if path.startswith("/branches"):
            return [{"name": b} for b in self.branches]
        if path.startswith("/pulls?state=open"):
            return [{"head": {"ref": h}} for h in self.open_heads]
        if "/check-runs" in path:
            return {"check_runs": [{"name": "worker-orchestration-tests", "conclusion": "success",
                                    "details_url": "https://github.com/cerniva/ai-shared-workspace/actions/runs/555/job/1"}]}
        raise AssertionError(path)


class Adapter:
    def __init__(self, text=None, exc=None):
        self.text, self.exc = text, exc

    def run(self, task):
        if self.exc:
            raise self.exc
        return {"recommendation": self.text}


GOOD = '{"slug":"ci-gate","lesson":"Gate merges on CI","decision":"Add required check","metric":"red merges/week"}'


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "knowledge").mkdir()
        (self.root / ll.LEDGER_REL).write_text("# L\n\n## 2026-10-01\n- a | PR #1 | b | c | d\n", encoding="utf-8")
        self.git_calls = []

    def tearDown(self):
        self.tmp.cleanup()

    def go(self, gh, adapter):
        return ll.run(7, gh=gh, env={"GITHUB_RUN_ID": "123"}, root=self.root, adapter=adapter,
                      git=self.git_calls.append)


class PureTests(unittest.TestCase):
    def test_extract_handoff(self):
        self.assertEqual(ll.extract_handoff_id(None, "x HO-20261010-12 y"), "HO-20261010-12")
        self.assertIsNone(ll.extract_handoff_id("HO-2026-1", ""))

    def test_build_line_format(self):
        line = ll.build_ledger_line("ci-gate", f"PR #7; merge {SHA[:7]}", "l|x lesson", "do it", "m m")
        self.assertRegex(line, r"^- ci-gate \| [^|]+ \| [^|]+ \| [^|]+ \| [^|]+$")
        self.assertEqual(line.count(" | "), 4)

    def test_rejects_placeholder_and_empty(self):
        ev = "PR #7"
        for args in [("ci", ev, "PLACEHOLDER", "d", "mmm"), ("ci", ev, "", "ddd", "mmm"),
                     ("ci", ev, "lll", "ddd", "  "), ("", ev, "lll", "ddd", "mmm"),
                     ("ci", "no evidence here", "lll", "ddd", "mmm"), ("placeholder", ev, "lll", "ddd", "mmm")]:
            with self.assertRaises(ll.LedgerLineError):
                ll.build_ledger_line(*args)

    def test_is_duplicate(self):
        self.assertTrue(ll.is_duplicate(f"x {SHA[:7]} y", 7, SHA))
        self.assertTrue(ll.is_duplicate("- a | PR #7 | b", 7, SHA))
        self.assertFalse(ll.is_duplicate("- a | PR #70 | b", 7, SHA))
        self.assertTrue(ll.is_duplicate("", 7, SHA, existing_branches=["bot/lessons-pr-7"]))
        self.assertTrue(ll.is_duplicate("", 7, SHA, open_pr_heads=["bot/lessons-pr-7"]))
        self.assertFalse(ll.is_duplicate("", 7, SHA))

    def test_should_skip(self):
        pr = {"merged": True, "base": {"ref": "main"}, "head": {"ref": "feat"}}
        self.assertIsNone(ll.should_skip(pr, ["a.py"]))
        self.assertIn("self-loop", ll.should_skip(pr, [ll.LEDGER_REL]))
        self.assertIn("self-loop", ll.should_skip({**pr, "head": {"ref": "bot/lessons-pr-3"}}, ["a.py"]))
        self.assertEqual(ll.should_skip({**pr, "merged": False}, ["a.py"]), "not merged")

    def test_append_to_ledger(self):
        t = "# L\n\n## 2026-10-01\n- a\n\n## 2026-10-02\n- b\n"
        out = ll.append_to_ledger(t, "- c", "2026-10-01")
        self.assertIn("## 2026-10-01\n- a\n- c\n\n## 2026-10-02", out)
        out2 = ll.append_to_ledger(t, "- c", "2026-10-10")
        self.assertTrue(out2.endswith("## 2026-10-10\n- c\n"))
        self.assertEqual(ll.append_to_ledger(out2, "- c", "2026-10-10"), out2)


class FlowTests(Base):
    def test_no_key_posts_yapamadim_and_writes_nothing(self):
        before = (self.root / ll.LEDGER_REL).read_text()
        gh = FakeGH()
        out = self.go(gh, None)
        self.assertEqual(out["status"], "yapamadim")
        self.assertEqual(len(gh.posts), 1)
        self.assertEqual(gh.posts[0][0], "/issues/7/comments")
        self.assertTrue(gh.posts[0][1]["body"].startswith("YAPAMADIM:"))
        self.assertEqual((self.root / ll.LEDGER_REL).read_text(), before)
        self.assertNotIn("PLACEHOLDER", (self.root / ll.LEDGER_REL).read_text())
        self.assertEqual(self.git_calls, [])

    def test_provider_error_and_invalid_output(self):
        for ad in (Adapter(exc=RuntimeError("down")), Adapter(text="not json"),
                   Adapter(text='{"slug":"x-y","lesson":"PLACEHOLDER","decision":"ddd","metric":"mmm"}')):
            gh = FakeGH()
            self.assertEqual(self.go(gh, ad)["status"], "yapamadim")
            self.assertTrue(gh.posts[0][1]["body"].startswith("YAPAMADIM:"))
        self.assertEqual(self.git_calls, [])

    def test_success_opens_pr_on_lessons_branch(self):
        gh = FakeGH()
        out = self.go(gh, Adapter(text=GOOD))
        self.assertEqual(out["status"], "opened")
        text = (self.root / ll.LEDGER_REL).read_text()
        self.assertIn("PR #7", text)
        self.assertIn(SHA[:7], text)
        self.assertIn("HO-20261010-03", text)
        self.assertIn(["push", "origin", "HEAD:refs/heads/bot/lessons-pr-7"], self.git_calls)
        self.assertFalse(any("main" in " ".join(c) for c in self.git_calls))
        path, body = gh.posts[0]
        self.assertEqual(path, "/pulls")
        self.assertEqual(body["title"], "knowledge(lessons): PR #7 dersi")
        self.assertEqual(body["base"], "main")

    def test_dedup_and_self_loop_skip(self):
        self.assertEqual(self.go(FakeGH(branches=["bot/lessons-pr-7"]), Adapter(text=GOOD))["status"], "skip")
        self.assertEqual(self.go(FakeGH(files=[ll.LEDGER_REL]), Adapter(text=GOOD))["status"], "skip")
        self.assertEqual(self.go(FakeGH(head="bot/lessons-pr-1"), Adapter(text=GOOD))["status"], "skip")
        (self.root / ll.LEDGER_REL).write_text("## 2026-10-01\n- a | PR #7 | b | c | d\n")
        self.assertEqual(self.go(FakeGH(), Adapter(text=GOOD))["status"], "skip")


class DispatchPathTests(Base):
    def test_parse_dispatch_payload(self):
        self.assertEqual(ll.parse_dispatch_payload({"pr_number": 12, "merge_sha": SHA}), 12)
        self.assertEqual(ll.parse_dispatch_payload({"pr_number": "34"}), 34)
        for bad in (None, {}, {"pr_number": ""}, {"pr_number": "x"}, {"pr_number": -1}, {"pr_number": 0}):
            self.assertIsNone(ll.parse_dispatch_payload(bad))

    def _main(self, argv, gh):
        import io, contextlib
        orig_gh, orig_run = ll.GH, ll.run
        seen = {}
        ll.GH = lambda *a, **k: gh
        ll.run = lambda n, **k: seen.setdefault("pr", n) and {"status": "fake"}
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = ll.main(argv, env={})
        finally:
            ll.GH, ll.run = orig_gh, orig_run
        return rc, buf.getvalue(), seen.get("pr")

    def test_main_uses_dispatch_payload(self):
        rc, _, pr = self._main(["--pr", "", "--dispatch-payload",
                                json.dumps({"pr_number": 7, "merge_sha": SHA, "handoff_id": "HO-20261010-03"})], FakeGH())
        self.assertEqual((rc, pr), (0, 7))

    def test_main_invalid_payload_skips_exit0(self):
        rc, out, pr = self._main(["--pr", "", "--dispatch-payload", "{bad"], FakeGH())
        self.assertEqual(rc, 0)
        self.assertIsNone(pr)
        self.assertIn("no valid pr_number", out)

    def test_dispatched_pr_same_dedup_and_self_loop(self):
        self.assertEqual(self.go(FakeGH(head="bot/lessons-pr-2"), Adapter(text=GOOD))["status"], "skip")
        self.assertEqual(self.go(FakeGH(files=[ll.LEDGER_REL]), Adapter(text=GOOD))["status"], "skip")
        self.assertEqual(self.go(FakeGH(open_heads=["bot/lessons-pr-7"]), Adapter(text=GOOD))["status"], "skip")

    def test_team_pr_opened_dispatch_after_pr(self):
        gh = FakeGH()
        out = self.go(gh, Adapter(text=GOOD))
        self.assertEqual(out["dispatched"], "team-pr-opened")
        self.assertEqual([p for p, _ in gh.posts], ["/pulls", "/dispatches"])
        body = gh.posts[-1][1]
        self.assertEqual(body["event_type"], "team-pr-opened")
        self.assertEqual(body["client_payload"], {"pr_number": 99, "head_sha": "feedbeef", "handoff_id": "HO-20261010-03"})


class GateContractTests(Base):
    """Lesson PRs must meet scripts/auto_merge_gate.py + config/auto_merge.json conditions."""

    def setUp(self):
        super().setUp()
        self.cfg = json.loads((Path(__file__).resolve().parents[1] / "config/auto_merge.json").read_text())

    def _opened(self, gh):
        self.assertEqual(self.go(gh, Adapter(text=GOOD))["status"], "opened")
        return gh.posts[0][1]

    def test_branch_prefix_draft_and_body_pass_gate_regexes(self):
        body = self._opened(FakeGH())
        self.assertTrue(any(body["head"].startswith(p) for p in self.cfg["allowed_head_prefixes"]))
        self.assertEqual(body["head"], "bot/lessons-pr-7")
        self.assertIs(body["draft"], False)
        self.assertEqual(re.search(self.cfg["handoff_regex"], body["body"]).group(0), "HO-20261010-03")
        self.assertRegex(body["body"], self.cfg["evidence_regex"])
        self.assertIn("\nCI: kaynak merge abcdef1", body["body"])
        self.assertIn("/actions/runs/555", body["body"])

    def test_no_handoff_id_opens_pr_but_gate_regex_fails(self):
        gh = FakeGH()
        gh.pr["title"] = "feat: no handoff"
        body = self._opened(gh)
        self.assertIsNone(re.search(self.cfg["handoff_regex"], body["body"]))
        self.assertIn("handoff: yok", body["body"])

    def test_dispatch_handoff_id_fallback(self):
        gh = FakeGH()
        gh.pr["title"] = "feat: no handoff"
        out = ll.run(7, gh=gh, env={"DISPATCH_HANDOFF_ID": "HO-20261010-09"}, root=self.root,
                     adapter=Adapter(text=GOOD), git=self.git_calls.append)
        self.assertEqual(out["status"], "opened")
        self.assertIn("HO-20261010-09", gh.posts[0][1]["body"])

    def test_ci_line_reports_failure_honestly(self):
        line = ll.ci_evidence_line(SHA, {"a": "failure"}, [])
        self.assertIn("a=failure", line)
        self.assertNotRegex(line, self.cfg["evidence_regex"])

    def test_only_ledger_changed_so_denylist_safe(self):
        self._opened(FakeGH())
        self.assertEqual([c for c in self.git_calls if c[0] == "add"], [["add", ll.LEDGER_REL]])


from datetime import datetime, timedelta, timezone  # noqa: E402

NOW = datetime(2026, 10, 10, 1, 0, tzinfo=timezone.utc)


def cand(n, days_ago=1, comments=("YAPAMADIM: sebep",), head="feat/x", sha=None):
    return {"number": n, "merge_sha": sha or f"{n:07d}" + "f" * 33, "head_ref": head,
            "merged_at": (NOW - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z"),
            "comments": list(comments)}


class BacklogSelectionTests(unittest.TestCase):
    def test_requires_yapamadim_and_window_and_limit(self):
        cs = [cand(1, 1), cand(2, 2), cand(3, 3), cand(4, 4), cand(5, 15), cand(6, 1, comments=("ok",))]
        self.assertEqual(ll.select_backlog(cs, "", now=NOW), [1, 2, 3])
        self.assertEqual(ll.select_backlog(cs, "", now=NOW, limit=10), [1, 2, 3, 4])

    def test_dedup_and_skip_existing_lessons(self):
        cs = [cand(1), cand(1), cand(2), cand(3), cand(4, comments=("YAPAMADIM: x", "Ders yazıldı: #9")),
              cand(5, head="bot/lessons-pr-1"), cand(6)]
        ledger = "- a | PR #2 | b | c | d\n"
        got = ll.select_backlog(cs, ledger, now=NOW, existing_branches=["bot/lessons-pr-3"],
                                open_pr_heads=["bot/lessons-pr-6"])
        self.assertEqual(got, [1])

    def test_skip_when_merge_sha_in_ledger(self):
        c = cand(8, sha="1234567" + "a" * 33)
        self.assertEqual(ll.select_backlog([c], "x 1234567 y", now=NOW), [])


class BacklogGH(FakeGH):
    def __init__(self, cands, **kw):
        super().__init__(**kw)
        self.cands = cands
        self.gets = []

    def call(self, method, path, body=None):
        self.gets.append((method, path))
        if method == "GET" and path.startswith("/pulls?state=closed"):
            return [{"number": c["number"], "merge_commit_sha": c["merge_sha"], "merged_at": c["merged_at"],
                     "head": {"ref": c["head_ref"]}} for c in self.cands]
        if method == "GET" and path.startswith("/issues/") and "/comments" in path:
            n = int(path.split("/")[2])
            return [{"body": b} for c in self.cands if c["number"] == n for b in c["comments"]]
        if method == "GET" and path.startswith("/pulls/") and not path.startswith("/pulls/7"):
            n = int(path.split("/")[2].split("?")[0])
            if path.endswith("files?per_page=100"):
                return [{"filename": "scripts/a.py"}]
            return {**self.pr, "number": n, "title": f"feat {n}", "merge_commit_sha": f"{n:07d}" + "e" * 33}
        return super().call(method, path, body)


class BacklogRunTests(Base):
    def test_no_key_does_nothing_exit0(self):
        gh = BacklogGH([cand(1)])
        out = ll.run_backlog(gh=gh, env={}, root=self.root, adapter=None, git=self.git_calls.append, now=NOW)
        self.assertEqual(out["status"], "skip")
        self.assertEqual(gh.gets, [])
        self.assertEqual(gh.posts, [])
        self.assertEqual(self.git_calls, [])

    def test_main_backlog_no_key_exit0(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = ll.main(["--backlog"], env={})
        self.assertEqual(rc, 0)
        self.assertIn("no provider key", buf.getvalue())

    def test_processes_max3_and_comments_done(self):
        gh = BacklogGH([cand(n, n) for n in (11, 12, 13, 14)])
        out = ll.run_backlog(gh=gh, env={}, root=self.root, adapter=Adapter(text=GOOD),
                             git=self.git_calls.append, now=NOW)
        self.assertEqual(out["picked"], [11, 12, 13])
        done = [(p, b["body"]) for p, b in gh.posts if p.startswith("/issues/")]
        self.assertEqual(done, [(f"/issues/{n}/comments", "Ders yazıldı: #99") for n in (11, 12, 13)])
        self.assertEqual(sum(1 for p, _ in gh.posts if p == "/pulls"), 3)

    def test_provider_fails_stops_without_new_yapamadim(self):
        gh = BacklogGH([cand(11), cand(12)])
        out = ll.run_backlog(gh=gh, env={}, root=self.root, adapter=Adapter(exc=RuntimeError("down")),
                             git=self.git_calls.append, now=NOW)
        self.assertEqual(len(out["results"]), 1)
        self.assertEqual(out["results"][0]["status"], "yapamadim")
        self.assertEqual(gh.posts, [])


class WorkflowTests(unittest.TestCase):
    def test_workflow_contract(self):
        wf = (Path(__file__).resolve().parents[1] / ".github/workflows/lesson-learner.yml").read_text()
        self.assertIn("merged == true", wf)
        self.assertIn("types: [closed]", wf)
        self.assertIn("workflow_dispatch", wf)
        self.assertIn("repository_dispatch:", wf)
        self.assertIn("types: [main-merged]", wf)
        self.assertNotIn("push:", wf)
        self.assertNotIn("models: read", wf)  # no GitHub Models adapter in shared provider_config yet
        self.assertNotIn("schedule", wf)
        self.assertIn("contents: write", wf)
        self.assertIn("pull-requests: write", wf)
        for bad in ll.PROTECTED_WORKFLOWS:
            self.assertNotIn(bad, wf)
        self.assertNotIn("git push", wf)
        self.assertIn("'bot/lessons-pr-'", wf)
        self.assertIn('workflows: ["provider-health"]', wf)
        self.assertIn("--backlog", wf)
        root = Path(__file__).resolve().parents[1]
        ph = (root / ".github/workflows/provider-health.yml").read_text()
        self.assertIn("name: provider-health", ph)


if __name__ == "__main__":
    unittest.main()
