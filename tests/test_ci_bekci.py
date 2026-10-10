from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import ci_bekci as cb  # noqa: E402

UNITTEST_LOG = """2026-10-10T01:00:00.1234567Z Run python3 -m unittest discover
2026-10-10T01:00:01.0000000Z ok
2026-10-10T01:00:02.0000000Z ======================================================================
2026-10-10T01:00:02.0000000Z FAIL: test_merge_gate (tests.test_auto_merge_gate.GateTests.test_merge_gate)
2026-10-10T01:00:02.1000000Z Traceback (most recent call last):
2026-10-10T01:00:02.2000000Z   File "/home/runner/work/x/x/tests/test_auto_merge_gate.py", line 42, in test_merge_gate
2026-10-10T01:00:02.3000000Z AssertionError: 'pass' != 'fail'
2026-10-10T01:00:03.0000000Z FAILED (failures=1)
2026-10-10T01:00:03.1000000Z ##[error]Process completed with exit code 1.
"""

IMPORT_LOG = """2026-10-10T02:00:00Z Traceback (most recent call last):
2026-10-10T02:00:00Z   File "/home/runner/work/a/a/scripts/foo.py", line 3, in <module>
2026-10-10T02:00:00Z ModuleNotFoundError: No module named 'yaml'
2026-10-10T02:00:00Z ##[error]Process completed with exit code 1.
"""


class ExtractionTests(unittest.TestCase):
    def test_errors_from_unittest_log(self):
        errs = cb.extract_errors(cb.tail(UNITTEST_LOG))
        self.assertIn("Traceback (most recent call last):", errs)
        self.assertIn("AssertionError: 'pass' != 'fail'", errs)
        self.assertIn("FAILED (failures=1)", errs)
        self.assertIn("Process completed with exit code 1.", errs)
        self.assertFalse(any(e.startswith("2026-") for e in errs), "timestamps stripped")

    def test_test_ids(self):
        ids = cb.extract_test_ids(cb.tail(UNITTEST_LOG))
        self.assertEqual(ids, ["test_merge_gate (tests.test_auto_merge_gate.GateTests.test_merge_gate)"])
        self.assertEqual(cb.extract_test_ids(["FAILED tests/test_a.py::test_b - assert 1 == 2"]),
                         ["tests/test_a.py::test_b"])

    def test_module_not_found(self):
        errs = cb.extract_errors(cb.tail(IMPORT_LOG))
        self.assertIn("ModuleNotFoundError: No module named 'yaml'", errs)
        self.assertEqual(cb.extract_test_ids(cb.tail(IMPORT_LOG)), [])

    def test_tail_limits(self):
        text = "\n".join(f"line {i}" for i in range(200))
        self.assertEqual(len(cb.tail(text)), cb.LOG_TAIL_LINES)
        self.assertEqual(cb.tail(text)[-1], "line 199")

    def test_summary_short(self):
        s = cb.summarize("wf", 5, [{"name": "test", "steps": ["Unit"]}], ["Error: x"], [])
        self.assertIn("test[Unit]", s)
        self.assertLessEqual(len(cb.summarize("w", 1, [], ["E" * 5000], [])), 900)


class SignatureTests(unittest.TestCase):
    def test_stable_across_timestamps_paths_numbers(self):
        a = cb.signature(["2026-10-10T01:00:00Z File /home/runner/work/a/b/x.py line 42 SyntaxError: bad"])
        b = cb.signature(["2026-11-01T09:09:09Z File /tmp/other/x.py line 77 SyntaxError: bad"])
        self.assertEqual(a, b)
        self.assertRegex(a, r"^[0-9a-f]{12}$")

    def test_test_id_wins_and_differs(self):
        errs = cb.extract_errors(cb.tail(UNITTEST_LOG))
        ids = cb.extract_test_ids(cb.tail(UNITTEST_LOG))
        self.assertEqual(cb.signature(errs, ids), cb.signature(["other"], ids))
        self.assertNotEqual(cb.signature(errs, ids), cb.signature(["ModuleNotFoundError: x"]))
        self.assertEqual(cb.signature([]), "none")

    def test_marker_roundtrip_and_dedup(self):
        sig = cb.signature(["Error: boom"])
        body = cb.marker("Upload-free wf", sig) + "\nbody"
        self.assertEqual(cb.parse_marker(body), ("Upload-free wf", sig))
        issues = [{"number": 1, "body": cb.marker("a", sig)}, {"number": 2, "body": cb.marker("b", sig)},
                  {"number": 3, "body": cb.marker("b", sig), "pull_request": {}}]
        self.assertEqual(cb.find_issue(issues, "b", sig)["number"], 2)
        self.assertIsNone(cb.find_issue(issues, "c", sig))

    def test_known_shas(self):
        issue = {"body": cb.sha_marker("a" * 40)}
        self.assertEqual(cb.known_shas(issue, [{"body": cb.sha_marker("b" * 40)}]), {"a" * 40, "b" * 40})


class ExclusionTests(unittest.TestCase):
    def test_excluded(self):
        for name in ("ci-bekci", "takipci-denetci", "auto-merge-gate", "team-worker", "Upload YouTube Short",
                     "shorts-publish", "payment-sync", "gumroad-x", "shopify-worker"):
            self.assertTrue(cb.is_excluded(name), name)
        for name in ("worker-orchestration-tests", "CodeQL code scanning", "shorts-render-tests"):
            self.assertFalse(cb.is_excluded(name), name)

    def test_workflow_list_matches_repo(self):
        wf_dir = ROOT / ".github" / "workflows"
        names = set()
        for p in wf_dir.glob("*.yml"):
            m = re.search(r"(?m)^name:\s*(.+?)\s*$", p.read_text(encoding="utf-8"))
            if m:
                names.add(m.group(1).strip("'\""))
        text = (wf_dir / "ci-bekci.yml").read_text(encoding="utf-8")
        block = text.split("workflows:", 1)[1].split("types:", 1)[0]
        listed = set(re.findall(r'-\s*"([^"]+)"', block))
        self.assertEqual(listed, {n for n in names if not cb.is_excluded(n)})


class CapAndCloseTests(unittest.TestCase):
    def test_daily_cap(self):
        issues = [{"created_at": "2026-10-10T01:00:00Z"}, {"created_at": "2026-10-10T05:00:00Z"},
                  {"created_at": "2026-10-09T23:59:59Z"}, {"created_at": "2026-10-10T06:00:00Z", "pull_request": {}}]
        self.assertEqual(cb.count_created_today(issues, "2026-10-10"), 2)
        self.assertTrue(cb.dispatch_allowed(1))
        self.assertTrue(cb.dispatch_allowed(3))
        self.assertFalse(cb.dispatch_allowed(4))

    def test_close_on_green(self):
        run = {"name": "worker-orchestration-tests", "conclusion": "success", "head_branch": "main", "event": "push"}
        self.assertTrue(cb.should_close_on_green(run))
        self.assertFalse(cb.should_close_on_green({**run, "head_branch": "bot/x"}))
        self.assertFalse(cb.should_close_on_green({**run, "conclusion": "failure"}))
        self.assertFalse(cb.should_close_on_green({**run, "event": "pull_request"}))
        self.assertFalse(cb.should_close_on_green({**run, "name": "ci-bekci"}))
        issues = [{"number": 1, "body": cb.marker("worker-orchestration-tests", "abc123abc123")},
                  {"number": 2, "body": cb.marker("other", "abc123abc123")}, {"number": 3, "body": "no marker"}]
        self.assertEqual([i["number"] for i in cb.issues_to_close(issues, "worker-orchestration-tests")], [1])


class FakeGH:
    def __init__(self, open_issues, all_issues, comments=None):
        self.open, self.all, self.comments, self.calls = open_issues, all_issues, comments or [], []

    def paged(self, path, max_pages=10):
        if "/jobs" in path:
            return [{"id": 9, "name": "test", "conclusion": "failure", "html_url": "u",
                     "steps": [{"name": "Unit", "conclusion": "failure"}, {"name": "ok", "conclusion": "success"}]}]
        if "/comments" in path:
            return self.comments
        return self.open if "state=open" in path else self.all

    def job_log(self, job_id):
        return UNITTEST_LOG

    def request(self, method, path, body=None):
        self.calls.append((method, path, body))
        return {"number": 77} if path == "/issues" else {}


RUN = {"id": 123, "name": "worker-orchestration-tests", "head_sha": "c" * 40, "conclusion": "failure",
       "head_branch": "main", "html_url": "https://x/runs/123"}


class FlowTests(unittest.TestCase):
    def test_new_signature_opens_issue_and_dispatches(self):
        gh = FakeGH([], [{"created_at": "2026-10-10T01:00:00Z"}])
        res = cb.handle_failure(gh, RUN, today="2026-10-10")
        self.assertEqual(res["action"], "opened")
        disp = [c for c in gh.calls if c[1] == "/dispatches"]
        self.assertEqual(len(disp), 1)
        p = disp[0][2]["client_payload"]
        self.assertEqual((p["handoff_id"], p["source"], p["run_id"]), ("CI-123", "ci-bekci", "123"))

    def test_cap_blocks_dispatch(self):
        gh = FakeGH([], [{"created_at": "2026-10-10T0%d:00:00Z" % i} for i in range(4)])
        res = cb.handle_failure(gh, RUN, today="2026-10-10")
        self.assertFalse(res["dispatched"])
        self.assertFalse(any(c[1] == "/dispatches" for c in gh.calls))

    def test_existing_same_sha_noop_new_sha_comment(self):
        ids = cb.extract_test_ids(cb.tail(UNITTEST_LOG))
        sig = cb.signature(cb.extract_errors(cb.tail(UNITTEST_LOG)), ids)
        issue = {"number": 5, "body": cb.marker(RUN["name"], sig) + cb.sha_marker(RUN["head_sha"])}
        gh = FakeGH([issue], [])
        self.assertEqual(cb.handle_failure(gh, RUN)["action"], "noop")
        self.assertEqual([c for c in gh.calls if c[0] == "POST" and c[1] != "/labels"], [])
        gh2 = FakeGH([issue], [])
        self.assertEqual(cb.handle_failure(gh2, {**RUN, "head_sha": "d" * 40})["action"], "commented")
        self.assertFalse(any(c[1] in ("/dispatches", "/issues") for c in gh2.calls))

    def test_excluded_run_ignored(self):
        gh = FakeGH([], [])
        self.assertEqual(cb.process_run(gh, {**RUN, "name": "team-worker"})["action"], "excluded")
        self.assertEqual(gh.calls, [])


if __name__ == "__main__":
    unittest.main()
