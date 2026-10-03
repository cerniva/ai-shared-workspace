from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
EXPECTED_GROUP = "repo-main-writers"


class WorkflowWriterConcurrencyTests(unittest.TestCase):
    def test_every_git_writer_uses_shared_queued_group(self) -> None:
        writers: list[str] = []
        failures: list[str] = []
        for path in sorted(WORKFLOWS.glob("*.yml")):
            text = path.read_text(encoding="utf-8")
            writes_main = re.search(r"(?m)^\s+git push(?:\s|$)", text) or "scripts/desk_notify_commit.py" in text
            if not writes_main:
                continue
            writers.append(path.name)
            block = re.search(r"(?ms)^concurrency:\n(?P<body>(?:^[ \t]+.*\n?)+)", text)
            body = block.group("body") if block else ""
            if f"group: {EXPECTED_GROUP}" not in body or "queue: max" not in body:
                failures.append(path.name)
            if "cancel-in-progress: true" in body:
                failures.append(path.name + " (cancel-in-progress)")
        self.assertGreater(len(writers), 0, "no repository-writing workflows discovered")
        self.assertEqual(failures, [], f"unsafe main writers: {failures}")


if __name__ == "__main__":
    unittest.main()
