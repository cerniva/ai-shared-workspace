#!/usr/bin/env python3
"""Commit the desk ledger onto latest main, retrying generated-file races.

desk-notify checks out the triggering SHA. A queued run can therefore commit
on a parent that already has a bot ledger commit. Those JSON files are
generated, so a rebase conflict is not hand-merged: reset to origin/main,
reconcile again, then push.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

LEDGER_PATHS = (
    "state/message_delivery.json",
    "state/desk_notify_health.json",
    "state/inbox_read.json",
)
COMMIT_MESSAGE = "desk-notify: persist delivery ledger"


def run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=check)


def publish_ledger(repo: Path, reconcile, attempts: int = 4) -> str:
    repo = Path(repo)
    run(["git", "config", "user.name", "desk-notify-bot"], repo)
    run(
        ["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"],
        repo,
    )
    last = "not-started"
    for attempt in range(1, attempts + 1):
        run(["git", "fetch", "origin", "main"], repo)
        run(["git", "reset", "--hard", "origin/main"], repo)
        reconcile(repo)
        run(["git", "add", *LEDGER_PATHS], repo)
        dirty = run(["git", "diff", "--cached", "--quiet"], repo, check=False)
        if dirty.returncode == 0:
            return "noop"
        if dirty.returncode != 1:
            raise RuntimeError(dirty.stderr or dirty.stdout or "git diff failed")
        run(["git", "commit", "-m", COMMIT_MESSAGE], repo)
        push = run(["git", "push", "origin", "HEAD:main"], repo, check=False)
        if push.returncode == 0:
            return "pushed"
        last = (push.stderr or push.stdout or "push rejected").strip()
        print(f"desk-notify commit attempt {attempt} rejected: {last}", file=sys.stderr)
    raise RuntimeError(f"desk-notify ledger push failed after {attempts} attempts: {last}")


def reconcile_live(repo: Path) -> None:
    run([sys.executable, "scripts/desk_bridge.py", "reconcile"], repo)
    run([sys.executable, "scripts/desk_health_normalize.py"], repo)


def main() -> int:
    repo = Path(os.environ.get("DESK_NOTIFY_REPO", ".")).resolve()
    publish_ledger(repo, reconcile_live)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"desk-notify commit failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
