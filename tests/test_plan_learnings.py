import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.plan_learnings import plan_learnings

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "shorts-free-build.yml"


def _ledger(root: Path, rows: list) -> Path:
    path = root / "learning_ledger.json"
    path.write_text(json.dumps({"schema_version": 1, "updated_at": None, "learnings": rows}), encoding="utf-8")
    return path


class PlanLearningsTests(unittest.TestCase):
    def test_returns_only_active_rows_tagged_for_plan(self):
        rows = [
            {"learning_id": "learn_a", "title": "A", "decision": "D-A", "plan_tags": ["video_shopify"], "source_ids": ["src_1"]},
            {"learning_id": "learn_b", "title": "B", "decision": "D-B", "plan_tags": ["finance"]},
            {"learning_id": "learn_c", "title": "C", "decision": "D-C", "plan_tags": ["video_shopify"], "status": "superseded"},
            {"learning_id": "learn_d", "title": "D", "decision": "D-D"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            result = plan_learnings("video/shopify", ledger_path=_ledger(Path(tmp), rows), catalog_path=Path(tmp) / "c.json")
        self.assertIsNone(result["error"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["learnings"], [{"learning_id": "learn_a", "title": "A", "decision": "D-A", "source_ids": ["src_1"]}])

    def test_finance_alias_maps_to_canonical_tag(self):
        rows = [{"learning_id": "learn_b", "title": "B", "decision": "D-B", "plan_tags": ["finance"]}]
        with tempfile.TemporaryDirectory() as tmp:
            result = plan_learnings("Finans", ledger_path=_ledger(Path(tmp), rows), catalog_path=Path(tmp) / "c.json")
        self.assertEqual([row["learning_id"] for row in result["learnings"]], ["learn_b"])

    def test_invalid_ledger_or_tag_reports_error_without_raising(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "learning_ledger.json"
            path.write_text(json.dumps({"schema_version": 2, "learnings": []}), encoding="utf-8")
            bad_ledger = plan_learnings("finance", ledger_path=path, catalog_path=Path(tmp) / "c.json")
            bad_tag = plan_learnings("unknown-plan", ledger_path=_ledger(Path(tmp), []), catalog_path=Path(tmp) / "c.json")
        self.assertIn("invalid learning ledger", bad_ledger["error"])
        self.assertEqual(bad_ledger["count"], 0)
        self.assertIsNotNone(bad_tag["error"])

    def test_cli_writes_report_for_repo_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "plan.json"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "plan_learnings.py"), "video_shopify", "--out", str(out)],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            report = json.loads(out.read_text(encoding="utf-8"))
        self.assertIsNone(report["error"])
        self.assertEqual(report["count"], len(report["learnings"]))

    def test_shorts_build_workflow_loads_and_uploads_plan_learnings(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("python3 scripts/plan_learnings.py video_shopify --require --out artifacts/plan_learnings.json", text)
        self.assertIn("artifacts/plan_learnings.json", text.split("Upload free build bundle", 1)[1])

    def test_require_fails_closed_when_plan_has_no_learnings(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = _ledger(Path(tmp), [])
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "plan_learnings.py"), "finance", "--require",
                 "--ledger", str(ledger), "--catalog", str(Path(tmp) / "c.json")],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        self.assertEqual(proc.returncode, 3)
        self.assertIn("bridge_failure", proc.stderr)

    def test_check_workflow_requires_every_plan(self):
        text = (ROOT / ".github" / "workflows" / "plan-learnings-check.yml").read_text(encoding="utf-8")
        for tag in ("finance", "video_shopify", "system"):
            self.assertIn(f"python3 scripts/plan_learnings.py {tag} --require", text)


if __name__ == "__main__":
    unittest.main()
