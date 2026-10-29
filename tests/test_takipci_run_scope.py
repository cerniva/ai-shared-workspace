"""Regression: historical CI citations must not mask or fail current-head gates."""
import unittest

from scripts import takipci_denetci as td

REPO = "cerniva/ai-shared-workspace"
HEAD = "current-head-sha"


def cited_run(run_id, conclusion, sha=HEAD, repo=REPO, status="completed"):
    return {
        "id": run_id,
        "ref_repo": None,
        "run": {
            "id": run_id,
            "status": status,
            "conclusion": conclusion,
            "head_sha": sha,
            "repository": {"full_name": repo},
        },
    }


class AuditorRunScopeTests(unittest.TestCase):
    def test_historical_main_failure_is_warning_not_current_pr_failure(self):
        reasons, warnings = td.check_run_refs(
            [cited_run(40682689517, "failure", "old-main-sha")], REPO, HEAD
        )
        self.assertEqual(reasons, [])
        self.assertTrue(any("40682689517" in w and "historical" in w for w in warnings))

    def test_historical_in_progress_run_is_warning_not_gate(self):
        # Live regression: main CodeQL run 40787996094 was in progress
        # while the auditor checked a different PR head.
        reasons, warnings = td.check_run_refs(
            [cited_run(40787996094, None, "38694cd24a22f35bcef14ebbacc3eeea30bd7e63",
                       status="in_progress")], REPO, HEAD
        )
        self.assertEqual(reasons, [])
        self.assertTrue(any("40787996094" in w and "historical" in w for w in warnings))

    def test_historical_skipped_run_is_warning_not_gate(self):
        # Live regression: unrelated main comms-watch 40787996127 was skipped.
        reasons, warnings = td.check_run_refs(
            [cited_run(40787996127, "skipped", "38694cd24a22f35bcef14ebbacc3eeea30bd7e63")],
            REPO, HEAD
        )
        self.assertEqual(reasons, [])
        self.assertTrue(any("40787996127" in w and "historical" in w for w in warnings))

    def test_current_head_failed_run_still_blocks(self):
        reasons, warnings = td.check_run_refs(
            [cited_run(40687999121, "failure")], REPO, HEAD
        )
        self.assertTrue(any("40687999121" in r for r in reasons))
        self.assertEqual(warnings, [])

    def test_current_head_pending_run_still_blocks(self):
        reasons, _ = td.check_run_refs(
            [cited_run(40687999121, None, status="in_progress")], REPO, HEAD
        )
        self.assertTrue(reasons)

    def test_missing_run_head_stays_fail_closed_even_on_success(self):
        # A completed/success run without head_sha cannot prove this PR's CI.
        for sha in (None, ""):
            with self.subTest(sha=sha):
                reasons, warnings = td.check_run_refs(
                    [cited_run(40687999121, "success", sha=sha)], REPO, HEAD
                )
                self.assertTrue(any("missing head_sha" in r for r in reasons))
                self.assertEqual(warnings, [])

    def test_missing_run_head_with_failure_also_blocks(self):
        reasons, _ = td.check_run_refs(
            [cited_run(40687999121, "failure", sha=None)], REPO, HEAD
        )
        self.assertTrue(reasons)

    def test_foreign_repository_still_blocks(self):
        reasons, _ = td.check_run_refs(
            [cited_run(40687999121, "failure", "old-main-sha", "other/repo")],
            REPO, HEAD
        )
        self.assertTrue(reasons)

    def test_missing_run_still_blocks(self):
        reasons, _ = td.check_run_refs(
            [{"id": 40687999121, "ref_repo": None, "run": None, "error": "HTTP 404"}],
            REPO, HEAD
        )
        self.assertTrue(reasons)

    def test_current_head_check_failure_still_blocks(self):
        checks = [{"name": "test", "status": "completed", "conclusion": "failure"}]
        self.assertTrue(td.check_head_checks(checks))

    def test_dispatch_pending_gate_unchanged(self):
        checks = [{"name": "test", "status": "in_progress", "conclusion": None}]
        self.assertTrue(td.check_ci_pending(checks, False, True))


    def test_adjacent_evidence_headers_are_independent(self):
        # The second CI line remains a real failure; it must not be counted
        # twice as a failure of the preceding successful Test record.
        body = "HO-1\\nTest: 801 passed\\nCI: historical run failed\\n"
        reasons = td.check_evidence_words(body)
        self.assertEqual(len(reasons), 1, reasons)
        self.assertIn("evidence line 3", reasons[0])

    def test_multiline_current_failure_still_blocks(self):
        # A continuation line with a real failed result remains fail-closed.
        body = "HO-1\\nTest: run summary\\ncurrent-head job failed\\n"
        reasons = td.check_evidence_words(body)
        self.assertEqual(len(reasons), 1, reasons)
        self.assertIn("evidence line 2", reasons[0])


if __name__ == "__main__":
    unittest.main()
