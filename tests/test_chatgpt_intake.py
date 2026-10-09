import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.chatgpt_intake import path_blockers, patch_paths, validate_all

PATCH = """--- a/scripts/demo.py
+++ b/scripts/demo.py
@@ -1 +1 @@
-VALUE = 1
+VALUE = 2
"""


class ChatgptIntakeTests(unittest.TestCase):
    def _repo(self, tmp: str) -> Path:
        repo = Path(tmp)
        (repo / "scripts").mkdir()
        (repo / "scripts" / "demo.py").write_text("VALUE = 1\n", encoding="utf-8")
        (repo / "intake" / "chatgpt").mkdir(parents=True)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        return repo

    def test_paths_are_parsed_and_policy_enforced(self):
        self.assertEqual(patch_paths(PATCH), ["scripts/demo.py"])
        self.assertEqual(path_blockers(["scripts/demo.py"]), [])
        self.assertTrue(path_blockers([".github/workflows/x.yml"])[0].startswith("denied_path"))
        self.assertTrue(path_blockers(["projects/payoutlens/a.py"])[0].startswith("denied_path"))
        self.assertTrue(path_blockers(["setup.py"])[0].startswith("outside_allowed"))
        self.assertEqual(path_blockers([]), ["no_paths"])

    def test_clean_patch_passes_apply_check_without_touching_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            (repo / "intake" / "chatgpt" / "ok.patch").write_text(PATCH, encoding="utf-8")
            [report] = validate_all(repo, run_tests=False)
            self.assertEqual(report["status"], "PASS", report)
            self.assertEqual((repo / "scripts" / "demo.py").read_text(encoding="utf-8"), "VALUE = 1\n")

    def test_stale_patch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(tmp)
            (repo / "scripts" / "demo.py").write_text("VALUE = 9\n", encoding="utf-8")
            (repo / "intake" / "chatgpt" / "stale.patch").write_text(PATCH, encoding="utf-8")
            [report] = validate_all(repo, run_tests=False)
            self.assertEqual(report["status"], "FAIL")
            self.assertIn("git_apply_check_failed", report["blockers"])

    def test_workflow_is_read_only(self):
        text = (Path(__file__).resolve().parents[1] / ".github" / "workflows" / "chatgpt-intake.yml").read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertNotIn("git push", text)


if __name__ == "__main__":
    unittest.main()
