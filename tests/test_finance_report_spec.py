import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC_JSON = ROOT / "projects" / "finance" / "report_spec.json"
SPEC_MD = ROOT / "projects" / "finance" / "REPORT_SPEC.md"

REQUIRED_CLASSES = {
    "precious_metals",
    "energy_oil",
    "industrial_metals",
    "crypto",
    "equities_indices",
    "bonds_rates",
    "funds_etfs",
    "fx",
    "macro_calendar",
    "finance_world_news",
}


class FinanceReportSpecTest(unittest.TestCase):
    def test_canonical_spec_locks_user_presentation_rules(self):
        data = json.loads(SPEC_JSON.read_text(encoding="utf-8"))
        text = SPEC_MD.read_text(encoding="utf-8")
        self.assertEqual(data["id"], "CORE-02-REPORT-SPEC")
        self.assertEqual(data["status"], "canonical")
        self.assertTrue(data["does_not_publish_market_data"])
        self.assertEqual(set(data["asset_classes"]), REQUIRED_CLASSES)
        presentation = data["presentation"]
        self.assertFalse(presentation["default_charts"])
        self.assertTrue(presentation["python_charts_forbidden"])
        self.assertFalse(presentation["base_100_default"])
        panel = presentation["altcoin_bull_panel"]
        self.assertFalse(panel["enabled_by_default"])
        self.assertEqual(
            panel["when_charts_requested"],
            "two_panels_each_normalized_0_100_bullish_support",
        )
        self.assertEqual(presentation["closing_marker"], "CHAT GPT ANALİZİ:")
        self.assertFalse(data["sources"]["invent_prices_or_news"])
        self.assertTrue(data["sources"]["access_must_be_proven"])
        self.assertIn("PayoutLens", data["excluded"])
        self.assertIn("CHAT GPT ANALİZİ:", text)
        self.assertIn("Do not generate charts with Python.", text)
        self.assertIn("two panels", text)
        self.assertIn("precious metals", text)


if __name__ == "__main__":
    unittest.main()
