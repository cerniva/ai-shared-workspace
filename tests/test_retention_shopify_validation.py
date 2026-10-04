import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from retention_shopify_validation import (
    validate_automated_delivery_date,
    validate_average_view_metrics,
    validate_inventory_available,
    validate_market_shipping_rates,
    validate_retention_query,
)


class ValidationTests(unittest.TestCase):
    def test_avd_excludes_loops_and_rejects_apv_over_100_as_loop_proof(self):
        ok = validate_average_view_metrics({"averageViewDuration": 12, "averageViewPercentage": 40})
        self.assertEqual(ok["status"], "accept")
        self.assertFalse(ok["loops_included"])
        bad = validate_average_view_metrics({"averageViewDuration": 12, "averageViewPercentage": 140})
        self.assertEqual(bad["status"], "reject")
        missing = validate_average_view_metrics({})
        self.assertEqual(missing["status"], "unknown")

    def test_retention_query_is_single_video(self):
        self.assertEqual(validate_retention_query(["abc"])["status"], "accept")
        self.assertTrue(validate_retention_query(["abc"], "ORGANIC")["organic_only"])
        self.assertFalse(validate_retention_query(["abc"])["organic_only"])
        self.assertEqual(validate_retention_query(["a", "b"])["status"], "reject")
        self.assertEqual(validate_retention_query([])["status"], "reject")

    def test_null_available_is_not_zero(self):
        unknown = validate_inventory_available(None)
        self.assertEqual(unknown["status"], "unknown")
        self.assertIsNone(unknown["sellable"])
        self.assertEqual(validate_inventory_available(0)["sellable"], 0)
        self.assertEqual(validate_inventory_available("0")["status"], "reject")

    def test_automated_delivery_date_eligibility(self):
        ok = validate_automated_delivery_date({
            "origin_country": "US",
            "destination_country": "US",
            "in_stock": True,
            "immediate_fulfillment": True,
            "prediction_days": 3,
        })
        self.assertEqual(ok["status"], "accept")
        cross = validate_automated_delivery_date({
            "origin_country": "US",
            "destination_country": "FR",
            "in_stock": True,
            "immediate_fulfillment": True,
            "prediction_days": 3,
        })
        self.assertEqual(cross["status"], "reject")
        late = validate_automated_delivery_date({
            "origin_country": "DE",
            "destination_country": "FR",
            "in_stock": True,
            "immediate_fulfillment": True,
            "prediction_days": 6,
        })
        self.assertEqual(late["status"], "manual_fallback")

    def test_market_rates_do_not_sum(self):
        result = validate_market_shipping_rates([{"amount": 4}, {"amount": 9}])
        self.assertEqual(result["amount"], 9)
        self.assertFalse(result["summed"])
        self.assertIsNone(validate_market_shipping_rates([])["amount"])


if __name__ == "__main__":
    unittest.main()
