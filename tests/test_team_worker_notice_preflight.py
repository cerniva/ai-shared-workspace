"""Verify the real team-worker workflow's early dispatch gate.

Notification-only team-work dispatches from comms-watch carry no handoff_id.
They must not run costly FFmpeg setup, while normal handoffs and push/health
triggers remain enabled. This executes the embedded bash, not a reimplementation.
"""
import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/team-worker.yml"


class TeamWorkerNoticePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        marker = "      - name: Preflight handoff workload\n"
        assert cls.workflow.count(marker) == 1, "preflight must appear exactly once"
        section = cls.workflow.split(marker, 1)[1]
        cls.preflight = section.split("\n      - ", 1)[0]
        assert "        run: |\n" in cls.preflight
        cls.script = textwrap.dedent(cls.preflight.split("        run: |\n", 1)[1])

    def _run(self, event, handoff_id):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "output"
            env = {**os.environ, "EVENT_NAME": event, "HANDOFF_ID": handoff_id,
                   "GITHUB_OUTPUT": str(output)}
            proc = subprocess.run(["bash", "-e", "-c", self.script], env=env,
                                  capture_output=True, text=True, check=False)
            return proc, output.read_text() if output.exists() else ""

    def test_notification_only_dispatch_skips_worker(self):
        proc, output = self._run("repository_dispatch", "")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("run_worker=false", output)
        self.assertIn("notification-only", proc.stdout)

    def test_real_handoff_dispatch_runs(self):
        proc, output = self._run("repository_dispatch", "CI-12345")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("run_worker=true", output)

    def test_non_dispatch_events_keep_existing_execution(self):
        for event in ("push", "workflow_run", "workflow_dispatch"):
            with self.subTest(event=event):
                proc, output = self._run(event, "")
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("run_worker=true", output)

    def test_gate_precedes_expensive_steps_and_guards_all(self):
        w = self.workflow
        self.assertLess(w.index("- name: Preflight handoff workload"),
                        w.index("- uses: actions/setup-python@v7"))
        self.assertLess(w.index("- name: Preflight handoff workload"),
                        w.index("- name: Install ffmpeg"))
        for name in ("- uses: actions/setup-python@v7", "- name: Install ffmpeg",
                     "- name: Run team-worker"):
            segment = w.split(name, 1)[1].split("\n      - ", 1)[0]
            self.assertIn("if: ${{ steps.workload.outputs.run_worker == 'true' }}", segment)
        self.assertIn("python3 -m scripts.team_worker", w)


if __name__ == "__main__":
    unittest.main()
