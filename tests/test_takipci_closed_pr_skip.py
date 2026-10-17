from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import takipci_denetci as td  # noqa: E402


class _FakeGH:
    repo = "cerniva/ai-shared-workspace"

    def __init__(self, pr: dict):
        self.pr = pr
        self.calls: list[str] = []

    def request(self, method, path, body=None):
        self.calls.append(path)
        if path.startswith("/pulls/") and path.count("/") == 2:
            return self.pr
        raise AssertionError(f"unexpected request {method} {path}")

    def paged(self, path):
        raise AssertionError(f"unexpected paged {path}")


class ClosedPrSkipTest(unittest.TestCase):
    def test_closed_unmerged_pr_is_skipped_without_fetching_files(self):
        gh = _FakeGH({"state": "closed", "merged": False, "head": {"sha": "607147b"}})
        res, head = td.audit_pr(gh, 229, dispatch=True, ci_pending=True)
        self.assertEqual(res["verdict"], "skip")
        self.assertEqual(res["reasons"], [])
        self.assertEqual(head, "607147b")
        self.assertEqual(gh.calls, ["/pulls/229"])

    def test_merged_pr_is_not_skipped(self):
        gh = _FakeGH({"state": "closed", "merged": True, "head": {"sha": "abc"},
                      "base": {"sha": "def"}})
        with self.assertRaises(AssertionError):
            td.audit_pr(gh, 1)

    def test_open_pr_is_not_skipped(self):
        gh = _FakeGH({"state": "open", "merged": False, "head": {"sha": "abc"},
                      "base": {"sha": "def"}})
        with self.assertRaises(AssertionError):
            td.audit_pr(gh, 1)


if __name__ == "__main__":
    unittest.main()
