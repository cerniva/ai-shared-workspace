"""Tests for scripts/takipci_denetci.py (pure functions, no network)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import takipci_denetci as td  # noqa: E402

GOOD_BODY = "Handoff: HO-20261010-77\n- Test: 12 passed\n"
CODE = "\n".join(f"x{i} = {i}" for i in range(40)) + "\n"


def f(name, old=None, new=None, status="modified"):
    return {"filename": name, "status": status, "old_text": old, "new_text": new}


class TakipciDenetciTests(unittest.TestCase):
    def test_check_name_matches_auto_merge_config(self):
        import json
        cfg = json.loads((ROOT / "config" / "auto_merge.json").read_text(encoding="utf-8"))
        self.assertEqual(td.CHECK_NAME, cfg["auditor_check_name"])

    def test_docs_only_feat_fails(self):
        res = td.evaluate("feat: new worker", [f("docs/x.md", "a\n", "a\nb\n"),
                                               f("knowledge/notes.md", None, "n\n", "added")],
                          GOOD_BODY, "bot/x")
        self.assertEqual(res["verdict"], "fail")
        self.assertTrue(any("feat/fix" in r for r in res["reasons"]))

    def test_docs_only_docs_title_passes(self):
        res = td.evaluate("docs: notes", [f("docs/x.md", "a\n", "a\nb\n")], GOOD_BODY, "bot/x")
        self.assertEqual(res["verdict"], "pass")

    def test_stub_marker_fails(self):
        res = td.evaluate("fix: x", [f("scripts/a.py", CODE, CODE + "# " + td.MARKERS[0] + "\n")],
                          GOOD_BODY, "bot/x")
        self.assertEqual(res["verdict"], "fail")
        self.assertTrue(any(td.MARKERS[0] in r for r in res["reasons"]))
        res = td.evaluate("fix: x", [f("scripts/a.py", CODE, CODE + td.MARKERS[1] + "\n")], GOOD_BODY, "bot/x")
        self.assertEqual(res["verdict"], "fail")

    def test_existing_marker_mentions_do_not_block_unrelated_fix(self):
        old = CODE + "# " + td.MARKERS[0] + "\\n"
        new = old + "fix_applied = True\\n"
        res = td.evaluate("fix: x", [f("scripts/a.py", old, new)], GOOD_BODY, "bot/x")
        self.assertEqual(res["verdict"], "pass", res["reasons"])

    def test_tmp_paste_line_fails(self):
        res = td.evaluate("fix: x", [f("scripts/a.py", CODE, CODE + td.TMP_PREFIX + "out.py\n")],
                          GOOD_BODY, "bot/x")
        self.assertEqual(res["verdict"], "fail")
        self.assertTrue(any(td.TMP_PREFIX in r for r in res["reasons"]))

    def test_big_shrink_fails(self):
        res = td.evaluate("fix: x", [f("scripts/a.py", CODE, "x = 1\ny = 2\nz = 3\nw = 4\nv = 5\nu = 6\n")],
                          GOOD_BODY, "bot/x")
        self.assertEqual(res["verdict"], "fail")
        self.assertTrue(any("shrank" in r for r in res["reasons"]))

    def test_shrink_below_min_lines_fails(self):
        old = "\n".join(f"a{i}" for i in range(8)) + "\n"
        res = td.evaluate("fix: x", [f(".github/workflows/w.yml", old, "a: 1\n")], GOOD_BODY, "bot/x")
        self.assertEqual(res["verdict"], "fail")

    def test_real_code_change_with_evidence_passes(self):
        res = td.evaluate("feat: add worker", [f("scripts/a.py", CODE, CODE + "y = 1\n"),
                                               f("tests/test_a.py", None, CODE, "added"),
                                               f("docs/a.md", "a\n", "b\n")],
                          GOOD_BODY, "bot/feature")
        self.assertEqual(res, {**res, "verdict": "pass", "reasons": [], "warnings": []})

    def test_missing_evidence_bot_fails_human_warns(self):
        files = [f("scripts/a.py", CODE, CODE + "y = 1\n")]
        bot = td.evaluate("feat: x", files, "no evidence", "bot/x")
        self.assertEqual(bot["verdict"], "fail")
        human = td.evaluate("feat: x", files, "no evidence", "feature/x")
        self.assertEqual(human["verdict"], "pass")
        self.assertEqual(len(human["warnings"]), 2)

    def test_commit_mode_skips_body(self):
        res = td.evaluate("feat: x", [f("scripts/a.py", CODE, CODE + "y\n")], check_pr_body=False)
        self.assertEqual(res["verdict"], "pass")

    def _run(self, rid, concl="success", sha="headsha1", repo="cerniva/ai-shared-workspace"):
        return {"id": rid, "ref_repo": None, "run": {"id": rid, "status": "completed", "conclusion": concl,
                                                     "head_sha": sha, "repository": {"full_name": repo}}}

    def _eval(self, body, runs=None, checks=None):
        return td.evaluate("feat: x", [f("scripts/a.py", CODE, CODE + "y = 1\n")], body, "bot/x",
                           run_refs=runs if runs is not None else [], head_checks=checks or [],
                           repo="cerniva/ai-shared-workspace", head_sha="headsha1")

    def test_extract_run_refs(self):
        body = ("CI: https://github.com/cerniva/ai-shared-workspace/actions/runs/38011158413 ok\n"
                "Test: run 38011185625 green, also #38011225554; not #123\n"
                "see https://github.com/other/repo/actions/runs/99999999\n")
        refs = td.extract_run_refs(body)
        self.assertEqual([r["id"] for r in refs], [38011158413, 99999999, 38011185625, 38011225554])
        self.assertEqual(refs[1]["repo"], "other/repo")

    def test_mixed_green_red_runs_fail(self):
        res = self._eval(GOOD_BODY, [self._run(11111111), self._run(22222222, "failure")])
        self.assertEqual(res["verdict"], "fail")
        self.assertTrue(any("22222222" in r for r in res["reasons"]))

    def test_all_green_runs_pass(self):
        res = self._eval(GOOD_BODY, [self._run(11111111), self._run(22222222)],
                         [{"name": "test", "status": "completed", "conclusion": "success"},
                          {"name": "takipci-denetci", "status": "completed", "conclusion": "failure"}])
        self.assertEqual(res["verdict"], "pass", res["reasons"])

    def test_foreign_or_missing_run_fails_and_sha_mismatch_warns(self):
        foreign = {"id": 3, "ref_repo": "other/repo", "run": None}
        self.assertEqual(self._eval(GOOD_BODY, [foreign])["verdict"], "fail")
        missing = {"id": 4, "ref_repo": None, "run": None, "error": "HTTP 404"}
        self.assertEqual(self._eval(GOOD_BODY, [missing])["verdict"], "fail")
        res = self._eval(GOOD_BODY, [self._run(5, sha="othersha")])
        self.assertEqual(res["verdict"], "pass")
        self.assertTrue(any("head_sha" in w for w in res["warnings"]))

    def test_red_word_in_ci_line_fails(self):
        for body in ("HO-1\nCI: build failed\n", "HO-1\nTest: kırmızı\n", "HO-1\n- CI: 3 FAILED\n",
                     "HO-1\nTest: see below\nfailure in step 3\n"):
            res = self._eval(body)
            self.assertEqual(res["verdict"], "fail", body)
        self.assertEqual(self._eval("HO-1\nTest: 42 passed, 0 failed\n")["verdict"], "pass")

    def test_failed_head_check_fails(self):
        for concl in ("failure", "cancelled", "timed_out"):
            res = self._eval(GOOD_BODY, checks=[{"name": "test", "status": "completed", "conclusion": concl}])
            self.assertEqual(res["verdict"], "fail", concl)
        res = self._eval(GOOD_BODY, checks=[{"name": "test", "status": "in_progress", "conclusion": None}])
        self.assertEqual(res["verdict"], "pass")

    def _dispatch(self, checks, ci_pending=False):
        return td.evaluate("feat: x", [f("scripts/a.py", CODE, CODE + "y = 1\n")], GOOD_BODY, "bot/x",
                           run_refs=[], head_checks=checks, repo="cerniva/ai-shared-workspace",
                           head_sha="headsha1", ci_pending=ci_pending, strict_pending=True)

    GREEN = [{"name": "test", "status": "completed", "conclusion": "success"},
             {"name": "takipci-denetci", "status": "in_progress", "conclusion": None},
             {"name": "auto-merge-gate", "status": "queued", "conclusion": None}]

    def test_dispatch_ci_pending_flag_fails(self):
        res = self._dispatch(self.GREEN, ci_pending=True)
        self.assertEqual(res["verdict"], "fail")
        self.assertTrue(any(r.startswith("ci_pending: CI not finished") for r in res["reasons"]))

    def test_dispatch_in_progress_check_fails(self):
        for st in ("in_progress", "queued"):
            res = self._dispatch(self.GREEN + [{"name": "codeql", "status": st, "conclusion": None}])
            self.assertEqual(res["verdict"], "fail", st)
            self.assertTrue(any("ci_pending" in r and "codeql" in r for r in res["reasons"]))

    def test_dispatch_all_done_green_passes(self):
        res = self._dispatch(self.GREEN)
        self.assertEqual(res["verdict"], "pass", res["reasons"])

    def test_pull_request_mode_ignores_in_progress(self):
        res = self._eval(GOOD_BODY, checks=[{"name": "codeql", "status": "in_progress", "conclusion": None}])
        self.assertEqual(res["verdict"], "pass")

    def test_workflow_passes_ci_pending_to_script(self):
        wf = (ROOT / ".github" / "workflows" / "takipci-denetci.yml").read_text(encoding="utf-8")
        self.assertIn("github.event.client_payload.ci_pending", wf)
        self.assertIn('--dispatch --ci-pending "${CP_CI_PENDING:-false}"', wf)


if __name__ == "__main__":
    unittest.main()
