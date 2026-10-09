from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import backup_supervisor as bs

NOW = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)


def _item(item_id, status="open", created="2026-10-10T08:00:00+00:00", **extra):
    base = {"id": item_id, "from": "chatgpt", "to": "grok", "task": "add a docs line", "reason_cannot_do": "r",
            "evidence": "e", "status": status, "created_at": created, "updated_at": created}
    base.update(extra)
    return base


class FakeAdapter:
    provider = "fake"

    def __init__(self, recommendation):
        self.recommendation = recommendation
        self.jobs = []

    def run(self, job):
        self.jobs.append(job)
        return {"provider": "deepseek", "recommendation": self.recommendation}


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        (self.root / "state").mkdir()
        (self.root / "docs").mkdir()
        (self.root / "docs" / "note.md").write_text("a\n", encoding="utf-8")
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)

    def _ledger(self, items):
        (self.root / "state" / "handoffs.json").write_text(
            json.dumps({"schema_version": 1, "items": items}), encoding="utf-8")

    def _run(self, adapter):
        return bs.run(env={}, root=self.root, adapter=adapter, ci={"available": False, "reason": "test"},
                      messages=[], now=NOW)

    def test_no_provider_skips_cleanly_and_writes_turkish_status(self):
        self._ledger([_item("HO-1")])
        rep = self._run(None)
        self.assertFalse(rep["provider_available"])
        self.assertEqual(rep["overdue"], ["HO-1"])
        text = (self.root / "messages" / "backup-supervisor-latest.md").read_text(encoding="utf-8")
        self.assertIn("anahtar yok", text)
        self.assertIn("HO-1", text)

    def test_order_and_missing_keys(self):
        self.assertEqual(bs.SUPERVISOR_ORDER, ("gemini", "deepseek", "claude", "openai"))
        self.assertIsNone(bs.supervisor_adapter(env={"XAI_API_KEY": "x"}))
        fa = bs.supervisor_adapter(env={"OPENAI_API_KEY": "o", "DEEPSEEK_API_KEY": "d", "GEMINI_API_KEY": "g"})
        self.assertEqual([a.provider for a in fa.adapters], ["gemini", "deepseek", "openai"])

    def test_safe_patch_written_to_intake_only_for_flagged_items(self):
        diff = "--- a/docs/note.md\n+++ b/docs/note.md\n@@ -1 +1,2 @@\n a\n+b\n"
        self._ledger([_item("HO-2", supervisor_ok=True), _item("HO-3")])
        fake = FakeAdapter("```diff\n" + diff + "```")
        rep = self._run(fake)
        self.assertEqual(len(fake.jobs), 1)
        self.assertEqual(rep["patches"][0]["path"], "intake/chatgpt/backup-supervisor-HO-2.patch")
        self.assertEqual((self.root / rep["patches"][0]["path"]).read_text(), diff)
        self.assertEqual((self.root / "docs" / "note.md").read_text(), "a\n")  # main untouched

    def test_blocked_paths_rejected(self):
        for path in (".github/workflows/x.yml", "projects/PayoutLens/a.py", "scripts/../.env"):
            diff = f"--- a/{path}\n+++ b/{path}\n@@ -0,0 +1 @@\n+x\n"
            self.assertTrue(bs.check_patch(diff, self.root), path)
        self._ledger([_item("HO-4", supervisor_ok=True)])
        bad = "--- a/.github/workflows/x.yml\n+++ b/.github/workflows/x.yml\n@@ -0,0 +1 @@\n+x\n"
        rep = self._run(FakeAdapter(bad))
        self.assertEqual(rep["patches"], [])
        self.assertEqual(rep["rejected"][0]["id"], "HO-4")

    def test_ci_status_never_crashes(self):
        self.assertFalse(bs.ci_status(None, None)["available"])
        def boom(url):
            raise OSError("net")
        self.assertFalse(bs.ci_status("o/r", "t", fetch=boom)["available"])
        ok = bs.ci_status("o/r", "t", fetch=lambda u: {"workflow_runs": [
            {"name": "a", "status": "completed", "conclusion": "failure", "id": 1},
            {"name": "b", "status": "completed", "conclusion": "success", "id": 2}]})
        self.assertEqual(ok["failing"], ["a"])

    def test_workflow_guards(self):
        root = Path(__file__).resolve().parents[1]
        text = (root / ".github/workflows/backup-supervisor.yml").read_text()
        self.assertIn("cron: '23 * * * *'", text)
        self.assertIn("actions/checkout@v7", text)
        self.assertIn("unexpected staged path", text)
        for name in ("GEMINI_API_KEY", "DEEPSEEK_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
            self.assertIn(f"secrets.{name}", text)


if __name__ == "__main__":
    unittest.main()
