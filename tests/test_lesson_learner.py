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
            return {"number": 99}
        if path == "/pulls/7":
            return self.pr
        if path.startswith("/pulls/7/files"):
            return [{"filename": f} for f in self.files]
        if path.startswith("/branches"):
            return [{"name": b} for b in self.branches]
        if path.startswith("/pulls?state=open"):
            return [{"head": {"ref": h}} for h in self.open_heads]
        if "/check-runs" in path:
            return {"check_runs": [{"name": "worker-orchestration-tests", "conclusion": "success"}]}
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
        self.assertTrue(ll.is_duplicate("", 7, SHA, existing_branches=["lessons/pr-7"]))
        self.assertTrue(ll.is_duplicate("", 7, SHA, open_pr_heads=["lessons/pr-7"]))
        self.assertFalse(ll.is_duplicate("", 7, SHA))

    def test_should_skip(self):
        pr = {"merged": True, "base": {"ref": "main"}, "head": {"ref": "feat"}}
        self.assertIsNone(ll.should_skip(pr, ["a.py"]))
        self.assertIn("self-loop", ll.should_skip(pr, [ll.LEDGER_REL]))
        self.assertIn("self-loop", ll.should_skip({**pr, "head": {"ref": "lessons/pr-3"}}, ["a.py"]))
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
        self.assertIn(["push", "origin", "HEAD:refs/heads/lessons/pr-7"], self.git_calls)
        self.assertFalse(any("main" in " ".join(c) for c in self.git_calls))
        path, body = gh.posts[-1]
        self.assertEqual(path, "/pulls")
        self.assertEqual(body["title"], "knowledge(lessons): PR #7 dersi")
        self.assertEqual(body["base"], "main")

    def test_dedup_and_self_loop_skip(self):
        self.assertEqual(self.go(FakeGH(branches=["lessons/pr-7"]), Adapter(text=GOOD))["status"], "skip")
        self.assertEqual(self.go(FakeGH(files=[ll.LEDGER_REL]), Adapter(text=GOOD))["status"], "skip")
        self.assertEqual(self.go(FakeGH(head="lessons/pr-1"), Adapter(text=GOOD))["status"], "skip")
        (self.root / ll.LEDGER_REL).write_text("## 2026-10-01\n- a | PR #7 | b | c | d\n")
        self.assertEqual(self.go(FakeGH(), Adapter(text=GOOD))["status"], "skip")


class PushPathTests(Base):
    def test_commit_message_parsing(self):
        self.assertEqual(ll.pr_number_from_commit_message("Merge pull request #12 from cerniva/feat\n\nx"), 12)
        self.assertEqual(ll.pr_number_from_commit_message("feat: thing (#34)\n\nbody"), 34)
        self.assertIsNone(ll.pr_number_from_commit_message("chore: direct push"))
        self.assertIsNone(ll.pr_number_from_commit_message("feat x\n\n(#5)"))

    def test_resolve_push_pr_api_fallback(self):
        class G:
            def call(self, m, path, body=None):
                assert path == f"/commits/{SHA}/pulls"
                return [{"number": 3, "merged_at": None, "base": {"ref": "main"}},
                        {"number": 9, "merged_at": "2026-10-10T00:00:00Z", "base": {"ref": "main"}}]
        self.assertEqual(ll.resolve_push_pr(SHA, "direct commit", G()), 9)
        self.assertEqual(ll.resolve_push_pr(SHA, "Merge pull request #4 from a/b", G()), 4)

        class E:
            def call(self, *a):
                raise RuntimeError("x")
        self.assertIsNone(ll.resolve_push_pr(SHA, "direct", E()))

    def test_push_main_no_pr_is_skip(self):
        class G:
            def call(self, *a):
                return []
        import io, contextlib
        orig = ll.GH
        ll.GH = lambda *a, **k: G()
        try:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = ll.main(["--push-sha", SHA], env={"HEAD_COMMIT_MESSAGE": "chore: x"})
        finally:
            ll.GH = orig
        self.assertEqual(rc, 0)
        self.assertIn("no merged PR", buf.getvalue())

    def test_push_resolved_pr_uses_same_dedup_and_self_loop(self):
        gh = FakeGH(head="lessons/pr-2", files=[ll.LEDGER_REL])
        n = ll.resolve_push_pr(SHA, "Merge pull request #7 from cerniva/lessons/pr-2", gh)
        self.assertEqual(n, 7)
        self.assertEqual(self.go(gh, Adapter(text=GOOD))["status"], "skip")
        self.assertEqual(self.go(FakeGH(open_heads=["lessons/pr-7"]), Adapter(text=GOOD))["status"], "skip")


class WorkflowTests(unittest.TestCase):
    def test_workflow_contract(self):
        wf = (Path(__file__).resolve().parents[1] / ".github/workflows/lesson-learner.yml").read_text()
        self.assertIn("merged == true", wf)
        self.assertIn("types: [closed]", wf)
        self.assertIn("workflow_dispatch", wf)
        self.assertIn("push:", wf)
        self.assertIn("--push-sha", wf)
        self.assertNotIn("schedule", wf)
        self.assertIn("contents: write", wf)
        self.assertIn("pull-requests: write", wf)
        for bad in ll.PROTECTED_WORKFLOWS:
            self.assertNotIn(bad, wf)
        self.assertNotIn("git push", wf)


if __name__ == "__main__":
    unittest.main()
