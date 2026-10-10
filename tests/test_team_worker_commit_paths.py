import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import team_worker as tw


def _git(root, *a):
    subprocess.run(["git", *a], cwd=root, check=True, capture_output=True)


class CommitPathspecsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        _git(self.root, "init", "-q")
        (self.root / "state").mkdir()
        (self.root / "state/handoffs.json").write_text("[]")

    def tearDown(self):
        self.tmp.cleanup()

    def test_missing_team_work_dir_is_skipped_and_add_succeeds(self):
        paths = tw.commit_pathspecs(self.root)
        self.assertEqual(paths, ["state/handoffs.json"])
        tw._git("add", "-A", *paths, cwd=self.root)  # must not raise pathspec error

    def test_existing_dir_and_queue_included(self):
        (self.root / tw.RESULT_DIR).mkdir(parents=True)
        (self.root / tw.RESULT_DIR / "x.json").write_text("{}")
        (self.root / tw.QUEUE).write_text("[]")
        self.assertEqual(tw.commit_pathspecs(self.root),
                         ["state/handoffs.json", tw.RESULT_DIR.as_posix(), tw.QUEUE.as_posix()])

    def test_tracked_but_deleted_dir_kept_so_deletion_is_staged(self):
        d = self.root / tw.RESULT_DIR
        d.mkdir(parents=True)
        (d / "x.json").write_text("{}")
        _git(self.root, "add", "-A")
        (d / "x.json").unlink()
        d.rmdir()
        self.assertIn(tw.RESULT_DIR.as_posix(), tw.commit_pathspecs(self.root))


if __name__ == "__main__":
    unittest.main()
