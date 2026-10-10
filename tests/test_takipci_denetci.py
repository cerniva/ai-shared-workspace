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


if __name__ == "__main__":
    unittest.main()
