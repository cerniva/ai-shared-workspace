import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "hercules_sentinel.json"
FIXTURES = ROOT / "tests" / "fixtures" / "hercules_sentinel"


class HerculesSentinelCliTests(unittest.TestCase):
    def _run(self, event: Path, report: Path, *extra: str):
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.validate_hercules_sentinel",
                "--contract",
                str(CONTRACT),
                "--event",
                str(event),
                "--report",
                str(report),
                *extra,
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def _write_variant(self, *, event_changes=None, report_changes=None):
        event = json.loads((FIXTURES / "event_workflow_failure.json").read_text(encoding="utf-8"))
        report = json.loads((FIXTURES / "report_valid.json").read_text(encoding="utf-8"))
        event.update(event_changes or {})
        report.update(report_changes or {})
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        event_path = root / "event.json"
        report_path = root / "report.json"
        event_path.write_text(json.dumps(event), encoding="utf-8")
        report_path.write_text(json.dumps(report), encoding="utf-8")
        return tmp, event_path, report_path

    def test_valid_fixture_exits_zero(self):
        result = self._run(FIXTURES / "event_workflow_failure.json", FIXTURES / "report_valid.json")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["valid"])

    def test_missing_required_field_exits_nonzero(self):
        tmp, event_path, report_path = self._write_variant()
        self.addCleanup(tmp.cleanup)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        del report["evidence"]
        report_path.write_text(json.dumps(report), encoding="utf-8")
        result = self._run(event_path, report_path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("evidence", result.stdout)

    def test_wrong_repo_exits_nonzero(self):
        tmp, event_path, report_path = self._write_variant(
            event_changes={"repository": "cerniva/grok-chatgpt-masa"},
            report_changes={"scope": "cerniva/grok-chatgpt-masa"},
        )
        self.addCleanup(tmp.cleanup)
        result = self._run(event_path, report_path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("repository", result.stdout)

    def test_forbidden_action_exits_nonzero(self):
        tmp, event_path, report_path = self._write_variant(
            event_changes={"requested_action": "merge"},
            report_changes={"forbidden_action_detected": True},
        )
        self.addCleanup(tmp.cleanup)
        result = self._run(event_path, report_path)
        self.assertNotEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["forbidden"])

    def test_malformed_json_exits_nonzero_without_leaking_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            event = root / "event.json"
            report = root / "report.json"
            event.write_text('{"repository": "cerniva/ai-shared-workspace"}', encoding="utf-8")
            report.write_text('{"secret": "DO_NOT_LEAK",', encoding="utf-8")
            result = self._run(event, report)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("DO_NOT_LEAK", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["valid"])


if __name__ == "__main__":
    unittest.main()
