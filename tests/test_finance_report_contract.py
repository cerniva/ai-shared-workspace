import json
import unittest
from pathlib import Path

from scripts.finance_report_contract import load_contract, validate_packet

ROOT = Path(__file__).resolve().parents[1]


def valid_packet():
    return {
        "asset_classes": ["metals", "crypto", "macro"],
        "charts": [
            {"asset_class": "metals", "normalization": "base-100", "index_base": 100},
            {"asset_class": "crypto", "normalization": "base-100", "index_base": 100},
        ],
        "altcoin_bull_panel": {"normalized_panels": 2, "normalization": "base-100"},
        "footer": "CHAT GPT ANALİZİ:",
        "sources": [{"source_id": "src_example", "provenance": "verified"}],
        "python_chart_generated": False,
        "live_prices_invented": False,
    }


class FinanceReportContractTests(unittest.TestCase):
    def test_contract_file_forbids_python_charts_and_live_generation(self):
        data = json.loads((ROOT / "projects/finance/report_contract.json").read_text(encoding="utf-8"))
        self.assertFalse(data["python_chart_generation"])
        self.assertFalse(data["live_market_generation"])
        self.assertEqual(data["report_footer_exact"], "CHAT GPT ANALİZİ:")
        self.assertEqual(data["chart_rules"]["altcoin_bull_panel"]["normalized_panels"], 2)
        loaded = load_contract()
        self.assertEqual(loaded["task_id"], "CORE-02")

    def test_valid_packet_has_no_errors(self):
        self.assertEqual(validate_packet(valid_packet()), [])

    def test_rejects_shared_metal_crypto_chart_and_python_plot(self):
        packet = valid_packet()
        packet["charts"] = [{"asset_class": "metals+crypto", "normalization": "base-100", "index_base": 100}]
        packet["python_chart_generated"] = True
        errors = validate_packet(packet)
        self.assertTrue(any("separate" in item or "share" in item for item in errors))
        self.assertTrue(any("python" in item for item in errors))

    def test_rejects_unverified_source_and_missing_footer(self):
        packet = valid_packet()
        packet["footer"] = "analiz"
        packet["sources"] = [{"source_id": "", "provenance": "unverified", "price": 100}]
        packet["altcoin_bull_panel"] = {"normalized_panels": 1, "normalization": "base-100"}
        errors = validate_packet(packet)
        self.assertTrue(any("footer" in item for item in errors))
        self.assertTrue(any("provenance" in item for item in errors))
        self.assertTrue(any("two normalized" in item for item in errors))
        self.assertTrue(any("invented prices" in item for item in errors))


if __name__ == "__main__":
    unittest.main()
