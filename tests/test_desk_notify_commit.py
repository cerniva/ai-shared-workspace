from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.desk_notify_commit import publish_ledger


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)


class DeskNotifyCommitTests(unittest.TestCase):
    def test_stale_checkout_resets_and_pushes_regenerated_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            origin = root / "origin.git"
            origin.mkdir()
            git(origin, "init", "--bare")
            seed = root / "seed"
            seed.mkdir()
            git(seed, "init", "-b", "main")
            git(seed, "config", "user.email", "seed@example.com")
            git(seed, "config", "user.name", "seed")
            (seed / "state").mkdir()
            (seed / "state" / "message_delivery.json").write_text("{}\n", encoding="utf-8")
            (seed / "state" / "desk_notify_health.json").write_text("{}\n", encoding="utf-8")
            (seed / "state" / "inbox_read.json").write_text("{}\n", encoding="utf-8")
            git(seed, "add", ".")
            git(seed, "commit", "-m", "seed")
            git(seed, "remote", "add", "origin", str(origin))
            git(seed, "push", "-u", "origin", "main")
            git(origin, "symbolic-ref", "HEAD", "refs/heads/main")

            stale = root / "stale"
            subprocess.run(["git", "clone", str(origin), str(stale)], check=True, capture_output=True)
            git(stale, "config", "user.email", "stale@example.com")
            git(stale, "config", "user.name", "stale")

            other = root / "other"
            subprocess.run(["git", "clone", str(origin), str(other)], check=True, capture_output=True)
            git(other, "config", "user.email", "other@example.com")
            git(other, "config", "user.name", "other")
            (other / "state" / "message_delivery.json").write_text('{"events":1}\n', encoding="utf-8")
            git(other, "add", ".")
            git(other, "commit", "-m", "desk-notify: persist delivery ledger")
            git(other, "push", "origin", "HEAD:main")

            def reconcile(repo: Path) -> None:
                (repo / "state" / "message_delivery.json").write_text('{"events":2}\n', encoding="utf-8")

            result = publish_ledger(stale, reconcile, attempts=3)
            self.assertEqual(result, "pushed")
            show = subprocess.run(
                ["git", "--git-dir", str(origin), "show", "main:state/message_delivery.json"],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(show.stdout, '{"events":2}\n')

    def test_workflow_uses_retrying_commit_script(self) -> None:
        text = Path(".github/workflows/desk-notify.yml").read_text(encoding="utf-8")
        self.assertIn("python3 scripts/desk_notify_commit.py", text)
        self.assertIn("queue: max", text)
        self.assertNotIn("git pull --rebase origin main", text)


if __name__ == "__main__":
    unittest.main()
