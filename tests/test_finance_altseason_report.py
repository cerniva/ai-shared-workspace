"""Finance decision artifact must contain applied learning, not just loader output."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.finance_altseason_report import produce
from projects.finance.altcoin_panel import FINANCE_ALTSEASON_LEARNING_ID

ROOT = Path(__file__).resolve().parents[1]


class FinanceAltseasonArtifactTests(unittest.TestCase):
    def test_cli_writes_real_decision_and_reads_it_back(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            values = base / "values.json"
            output = base / "decision.json"
            values.write_text(json.dumps({"btc_dominance": 50.0}), encoding="utf-8")
            run = subprocess.run(
                [sys.executable, "-m", "scripts.finance_altseason_report",
                 "--values-json", str(values), "--output-json", str(output)],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(output.is_file())
            decision = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(decision["applied_learning_ids"], [FINANCE_ALTSEASON_LEARNING_ID])
            from scripts.plan_learnings import plan_learnings
            active = {row["learning_id"]: row for row in plan_learnings("finance")["learnings"]}
            self.assertEqual(decision["applied_learning_source_ids"], {
                FINANCE_ALTSEASON_LEARNING_ID:
                    sorted(set(active[FINANCE_ALTSEASON_LEARNING_ID]["source_ids"]))})
            self.assertEqual(decision["composite_score"], "N/A")
            self.assertEqual(decision["scored"], 0)
            self.assertTrue(all(x["score"] == "N/A" for x in decision["indicators"].values()))

    @patch("scripts.plan_learnings.plan_learnings")
    def test_missing_learning_does_not_create_or_replace_artifact(self, loader):
        loader.return_value = {"tag": "finance", "error": None, "learnings": []}
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            values = base / "values.json"
            output = base / "decision.json"
            values.write_text("{}", encoding="utf-8")
            output.write_text("previous verified report", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "bridge_failure"):
                produce(values, output)
            self.assertEqual(output.read_text(encoding="utf-8"), "previous verified report")

    def test_nonfinite_input_fails_before_artifact_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            values = base / "values.json"
            output = base / "decision.json"
            values.write_text('{"indicator": 1e999}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "finite numeric"):
                produce(values, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
