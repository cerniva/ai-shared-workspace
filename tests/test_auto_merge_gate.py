"""Tests for scripts/auto_merge_gate.py with a mocked GitHub API."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import auto_merge_gate as amg  # noqa: E402

REPO = "cerniva/ai-shared-workspace"
GOOD_BODY = "Handoff: HO-20261010-99\n- Test: 42 passed\n"


class FakeGitHub(amg.GitHub):
    def __init__(self, pr=None, files=None, runs=None, statuses=None):
        super().__init__(REPO, "x")
        self.pr = pr or make_pr()
        self.files = files if files is not None else ["scripts/foo.py"]
        self.runs = runs if runs is not None else [
            {"name": "test", "status": "completed", "conclusion": "success"},
            {"name": "takipci-denetci", "status": "completed", "conclusion": "success"},
            {"name": "auto-merge-gate", "status": "in_progress", "conclusion": None},
        ]
        self.statuses = statuses or []
        self.comments: list[dict] = []
        self.calls: list[tuple] = []

    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        if method == "GET" and path == f"/pulls/{self.pr['number']}":
            return self.pr
        if method == "GET" and path.startswith("/commits/") and path.endswith("/status"):
            return {"statuses": self.statuses}
        if method == "GET" and "/check-runs" in path:
            return {"check_runs": self.runs if "page=1" in path else []}
        if method == "GET" and "/files" in path:
            return [{"filename": f} for f in self.files] if "page=1" in path else []
        if method == "GET" and "/comments" in path:
            return list(self.comments) if "page=1" in path else []
        if method == "POST" and path.endswith("/comments"):
            self.comments.append({"id": len(self.comments) + 1, "body": body["body"]})
            return {}
        if method == "PATCH" and path.startswith("/issues/comments/"):
            cid = int(path.rsplit("/", 1)[1])
            for c in self.comments:
                if c["id"] == cid:
                    c["body"] = body["body"]
            return {}
        if method == "PUT" and path.endswith("/merge"):
            return {"merged": True, "sha": "mergesha123"}
        if method == "POST" and path == "/dispatches":
            return {}
        raise AssertionError(f"unexpected call {method} {path}")

    def did(self, method, suffix):
        return [c for c in self.calls if c[0] == method and c[1].endswith(suffix)]


def make_pr(**kw):
    pr = {"number": 7, "state": "open", "draft": False, "title": "t", "body": GOOD_BODY,
          "head": {"ref": "bot/x", "sha": "abc", "repo": {"full_name": REPO}}}
    pr.update(kw)
    return pr


class AutoMergeGateTests(unittest.TestCase):
    def setUp(self):
        self.cfg = amg.load_config()

    def run_gate(self, gh):
        return amg.process_pr(gh, 7, self.cfg)

    def assert_no_merge(self, gh, res, needle):
        self.assertFalse(res["merge"])
        self.assertEqual(gh.did("PUT", "/merge"), [])
        self.assertEqual(gh.did("POST", "/dispatches"), [])
        self.assertEqual(len(gh.comments), 1)
        self.assertIn(needle, gh.comments[0]["body"])

    def test_green_evidence_clean_merges_and_dispatches(self):
        gh = FakeGitHub()
        res = self.run_gate(gh)
        self.assertTrue(res.get("merged"))
        merge = gh.did("PUT", "/merge")
        self.assertEqual(merge[0][2]["merge_method"], "squash")
        disp = gh.did("POST", "/dispatches")
        self.assertEqual(disp[0][2], {"event_type": "main-merged", "client_payload": {
            "pr_number": 7, "merge_sha": "mergesha123", "handoff_id": "HO-20261010-99"}})
        self.assertEqual(gh.comments, [])

    def test_missing_auditor_check_no_merge(self):
        gh = FakeGitHub(runs=[{"name": "test", "status": "completed", "conclusion": "success"}])
        self.assert_no_merge(gh, self.run_gate(gh), "takipci-denetci")

    def test_workflow_file_changed_no_merge(self):
        gh = FakeGitHub(files=["scripts/a.py", ".github/workflows/x.yml"])
        self.assert_no_merge(gh, self.run_gate(gh), ".github/workflows/x.yml")

    def test_payment_and_publish_paths_denied(self):
        for f in ["scripts/payout_report.py", "shopify_worker/x.py", "scripts/youtube_upload.py",
                  "config/meta_bridge.json", "shorts/shorts_publish.py", "scripts/shorts-free-render.sh",
                  "config/secrets.json"]:
            self.assertEqual(amg.denied_files([f], self.cfg["denylist"]), [f], f)
        self.assertEqual(amg.denied_files(["scripts/foo.py"], self.cfg["denylist"]), [])

    def test_missing_evidence_no_merge(self):
        gh = FakeGitHub(pr=make_pr(body="just a change"))
        self.assert_no_merge(gh, self.run_gate(gh), "HO-")

    def test_draft_no_merge(self):
        gh = FakeGitHub(pr=make_pr(draft=True))
        self.assert_no_merge(gh, self.run_gate(gh), "draft")

    def test_non_bot_branch_no_merge(self):
        gh = FakeGitHub(pr=make_pr(head={"ref": "feature/x", "sha": "abc", "repo": {"full_name": REPO}}))
        self.assert_no_merge(gh, self.run_gate(gh), "feature/x")

    def test_pending_or_failed_ci_no_merge(self):
        gh = FakeGitHub(runs=[
            {"name": "test", "status": "in_progress", "conclusion": None},
            {"name": "takipci-denetci", "status": "completed", "conclusion": "success"}])
        self.assert_no_merge(gh, self.run_gate(gh), "tamamlanmadı")
        gh = FakeGitHub(runs=[
            {"name": "test", "status": "completed", "conclusion": "failure"},
            {"name": "takipci-denetci", "status": "completed", "conclusion": "success"}])
        self.assert_no_merge(gh, self.run_gate(gh), "failure")

    def test_comment_idempotent(self):
        gh = FakeGitHub(pr=make_pr(draft=True))
        self.run_gate(gh)
        self.assertEqual(amg.process_pr(gh, 7, self.cfg)["comment"], "unchanged")
        self.assertEqual(len(gh.comments), 1)
        gh.pr["body"] = "no evidence"
        self.assertEqual(amg.process_pr(gh, 7, self.cfg)["comment"], "updated")
        self.assertEqual(len(gh.comments), 1)
        self.assertEqual(len(gh.did("POST", "/comments")), 1)

    # --- en son check run / status sayılır ---
    @staticmethod
    def _run(name, concl, ts, rid):
        return {"id": rid, "name": name, "status": "completed", "conclusion": concl,
                "started_at": ts, "completed_at": ts}

    def _base_runs(self):
        return [self._run("test", "success", "2026-10-10T00:00:00Z", 1),
                {"name": "auto-merge-gate", "status": "in_progress", "conclusion": None}]

    def test_old_red_new_green_same_name_merges(self):
        runs = self._base_runs() + [
            self._run("takipci-denetci", "failure", "2026-10-10T01:00:00Z", 10),
            self._run("takipci-denetci", "success", "2026-10-10T02:00:00Z", 11)]
        gh = FakeGitHub(runs=runs)
        res = self.run_gate(gh)
        self.assertTrue(res.get("merged"))
        self.assertEqual(len(gh.did("PUT", "/merge")), 1)

    def test_old_red_new_green_reversed_order_merges(self):
        runs = self._base_runs() + [
            self._run("takipci-denetci", "success", "2026-10-10T02:00:00Z", 11),
            self._run("takipci-denetci", "failure", "2026-10-10T01:00:00Z", 10)]
        gh = FakeGitHub(runs=runs)
        self.assertTrue(self.run_gate(gh).get("merged"))

    def test_old_green_new_red_same_name_no_merge(self):
        runs = self._base_runs() + [
            self._run("takipci-denetci", "success", "2026-10-10T01:00:00Z", 10),
            self._run("takipci-denetci", "failure", "2026-10-10T02:00:00Z", 11)]
        gh = FakeGitHub(runs=runs)
        self.assert_no_merge(gh, self.run_gate(gh), "takipci-denetci")

    def test_rerun_ci_old_green_new_red_no_merge(self):
        runs = [self._run("test", "success", "2026-10-10T00:00:00Z", 1),
                self._run("test", "failure", "2026-10-10T00:30:00Z", 2),
                self._run("takipci-denetci", "success", "2026-10-10T01:00:00Z", 10)]
        gh = FakeGitHub(runs=runs)
        self.assert_no_merge(gh, self.run_gate(gh), "test")

    def test_different_names_one_red_no_merge(self):
        runs = self._base_runs() + [
            self._run("takipci-denetci", "success", "2026-10-10T02:00:00Z", 11),
            self._run("lint", "failure", "2026-10-10T02:00:00Z", 12)]
        gh = FakeGitHub(runs=runs)
        self.assert_no_merge(gh, self.run_gate(gh), "lint")

    def test_status_latest_per_context(self):
        old_red = {"id": 1, "context": "ext", "state": "failure", "updated_at": "2026-10-10T01:00:00Z"}
        new_green = {"id": 2, "context": "ext", "state": "success", "updated_at": "2026-10-10T02:00:00Z"}
        gh = FakeGitHub(statuses=[old_red, new_green])
        self.assertTrue(self.run_gate(gh).get("merged"))
        old_green = dict(new_green, updated_at="2026-10-10T00:00:00Z")
        gh = FakeGitHub(statuses=[old_green, old_red])
        self.assert_no_merge(gh, self.run_gate(gh), "ext")


if __name__ == "__main__":
    unittest.main()
