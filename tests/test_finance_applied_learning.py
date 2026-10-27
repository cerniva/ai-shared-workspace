"""Finance altseason decision must consume active, source-linked learning, not a loader artifact."""
import copy
import unittest
from unittest.mock import patch

from projects.finance import altcoin_panel as ap


class FinanceAppliedLearningTests(unittest.TestCase):
    def setUp(self):
        self.cfg = ap.load_calibration_config()
        self.values = {row["name"]: 50.0 for row in self.cfg["indicators"]}

    def test_actual_decision_output_records_learning_and_blocks_unvalidated_scores(self):
        out = ap.altseason_panel(self.values, self.cfg)
        self.assertEqual(out["applied_learning_ids"], [ap.FINANCE_ALTSEASON_LEARNING_ID])
        self.assertEqual(out["scored"], 0)
        self.assertEqual(out["composite_score"], "N/A")
        self.assertTrue(all(row["score"] == "N/A" for row in out["indicators"].values()))

    @patch("scripts.plan_learnings.plan_learnings")
    def test_missing_active_learning_blocks_decision(self, mock_loader):
        mock_loader.return_value = {"tag": "finance", "error": None, "learnings": []}
        with self.assertRaisesRegex(ValueError, "bridge_failure"):
            ap.altseason_panel(self.values, self.cfg)

    @patch("scripts.plan_learnings.plan_learnings")
    def test_loader_error_blocks_decision(self, mock_loader):
        mock_loader.return_value = {"tag": "finance", "error": "missing ledger", "learnings": []}
        with self.assertRaisesRegex(ValueError, "bridge_failure"):
            ap.altseason_panel(self.values, self.cfg)

    @patch("scripts.plan_learnings.plan_learnings")
    def test_source_or_policy_drift_blocks_decision(self, mock_loader):
        row = {"learning_id": ap.FINANCE_ALTSEASON_LEARNING_ID,
               "source_ids": [], "decision": "No invented 0-100 values p20 p80 730"}
        mock_loader.return_value = {"tag": "finance", "error": None, "learnings": [row]}
        with self.assertRaisesRegex(ValueError, "source-linked"):
            ap.altseason_panel(self.values, self.cfg)
        row["source_ids"] = ["src_6c5b905f2e76e38d"]
        row["decision"] = "different rule"
        with self.assertRaisesRegex(ValueError, "policy changed"):
            ap.altseason_panel(self.values, self.cfg)

    @patch("scripts.plan_learnings.plan_learnings")
    def test_forged_source_id_blocks_actual_decision(self, mock_loader):
        mock_loader.return_value = {"tag": "finance", "error": None, "learnings": [{
            "learning_id": ap.FINANCE_ALTSEASON_LEARNING_ID,
            "source_ids": ["src_nonexistent"],
            "decision": "No invented 0-100 values p20 p80 730",
        }]}
        with self.assertRaisesRegex(ValueError, "unknown source_ids"):
            ap.altseason_panel(self.values, self.cfg)

    @patch("scripts.plan_learnings.plan_learnings")
    def test_duplicate_active_learning_blocks_decision(self, mock_loader):
        row = {"learning_id": ap.FINANCE_ALTSEASON_LEARNING_ID,
               "source_ids": ["src_6c5b905f2e76e38d"],
               "decision": "No invented 0-100 values p20 p80 730"}
        mock_loader.return_value = {"tag": "finance", "error": None,
                                    "learnings": [row, copy.deepcopy(row)]}
        with self.assertRaisesRegex(ValueError, "bridge_failure: .*duplicate"):
            ap.altseason_panel(self.values, self.cfg)

    def test_calibration_drift_blocks_decision(self):
        cfg = copy.deepcopy(self.cfg)
        cfg["calibration"]["min_coverage"] = 0.5
        with self.assertRaisesRegex(ValueError, "calibration parameters"):
            ap.altseason_panel(self.values, cfg)


if __name__ == "__main__":
    unittest.main()
