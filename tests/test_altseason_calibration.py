import json
import unittest
from pathlib import Path

from projects.finance import altcoin_panel as ap

ROOT = Path(__file__).resolve().parents[1]
PROMO = ROOT / "knowledge" / "promotions" / "2026-10-10-altseason-source-audit-calibration.json"


class AltseasonCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.cfg = ap.load_calibration_config()
        self.params = self.cfg["calibration"]

    def test_config_has_ten_indicators_with_directions_and_nothing_validated(self):
        inds = self.cfg["indicators"]
        self.assertEqual(len(inds), 10)
        self.assertEqual(self.params["train_days"], 730)
        self.assertEqual((self.params["lo_pct"], self.params["hi_pct"]), (20, 80))
        by = {i["name"]: i for i in inds}
        self.assertEqual(by["btc_dominance"]["direction"], "lower_is_bullish")
        self.assertEqual(by["altseason_index"]["direction"], "higher_is_bullish")
        self.assertEqual(by["funding_and_oi_excess"]["direction"], "nonmonotonic")
        self.assertFalse(any(i["validated"] for i in inds))
        self.assertTrue(all(i["source_url"].startswith("https://") for i in inds))

    def test_uncalibrated_panel_is_all_na(self):
        out = ap.altseason_panel({i["name"]: 50.0 for i in self.cfg["indicators"]}, self.cfg)
        self.assertEqual(out["scored"], 0)
        self.assertEqual(out["composite_score"], "N/A")

    def test_validated_indicator_scores_and_direction_applies(self):
        cfg = json.loads(json.dumps(self.cfg))
        for ind in cfg["indicators"]:
            if ind["name"] == "btc_dominance":
                ind.update(lo=40.0, hi=60.0, validated=True)
        out = ap.altseason_panel({"btc_dominance": 45.0}, cfg)
        self.assertEqual(out["indicators"]["btc_dominance"]["score"], 75.0)
        self.assertEqual(out["indicators"]["altseason_index"]["score"], "N/A")
        self.assertEqual(out["composite_score"], "N/A")

    def test_nonmonotonic_stays_na_even_if_validated(self):
        cfg = json.loads(json.dumps(self.cfg))
        for ind in cfg["indicators"]:
            ind.update(lo=0, hi=1, validated=True)
        out = ap.altseason_panel({i["name"]: 0.5 for i in cfg["indicators"]}, cfg)
        self.assertEqual(out["indicators"]["funding_and_oi_excess"]["score"], "N/A")
        self.assertEqual(out["composite_score"], "N/A")

    def test_train_bounds_p20_p80_no_lookahead_and_coverage(self):
        hist = [float(i % 100) for i in range(900)]
        self.assertIsNone(ap.fit_train_bounds(hist, 729, self.params))  # early fold
        lo, hi = ap.fit_train_bounds(hist, 800, self.params)
        self.assertTrue(19 <= lo <= 21 and 79 <= hi <= 81, (lo, hi))
        poisoned = hist[:800] + [1e9] * 100
        self.assertEqual(ap.fit_train_bounds(poisoned, 800, self.params), (lo, hi))
        sparse = [None if i % 2 else v for i, v in enumerate(hist)]
        self.assertIsNone(ap.fit_train_bounds(sparse, 800, self.params))
        self.assertIsNone(ap.fit_train_bounds([5.0] * 900, 800, self.params))  # p20 == p80

    def test_promotion_is_honest(self):
        doc = json.loads(PROMO.read_text(encoding="utf-8"))
        row = doc["learnings"][0]
        self.assertEqual(row["provenance"], "unverified")
        self.assertEqual(row["outcome"], "pending")
        self.assertEqual(set(row["source_ids"]), {s["source_id"] for s in doc["sources"]})


if __name__ == "__main__":
    unittest.main()
