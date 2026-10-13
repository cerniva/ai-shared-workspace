"""Unit tests for the read-only Shopify margin screen."""
import unittest
from scripts.shopify_margin_gate import audit_variant


def sample():
    return {
        "status": "DRAFT", "price": "24.90", "unit_cost": "7.42",
        "price_currency": "EUR", "cost_currency": "EUR",
        "unit_cost_verified": True, "rights_verified": True,
        "requires_shipping": True, "weight_verified": True,
        "weight_kg": "0.45", "shipping_cost": "4.20",
        "payment_fees": "1.00", "return_reserve": "1.00",
        "tax_reserve": "2.00", "demand_evidence_verified": True,
        "evidence": {k: "independent documented source" for k in (
            "unit_cost", "rights", "payment_fees", "returns", "taxes",
            "demand", "shipping", "weight")},
    }


class MarginGateTests(unittest.TestCase):
    def test_positive_is_review_only(self):
        self.assertEqual(audit_variant(sample())["status"], "REVIEW_ONLY")

    def test_equal_cost_blocks(self):
        row = sample()
        row["unit_cost"] = row["price"]
        self.assertEqual(audit_variant(row)["status"], "BLOCK_NONPOSITIVE_SPREAD")

    def test_missing_shipping_blocks(self):
        row = sample()
        row["shipping_cost"] = None
        self.assertEqual(audit_variant(row)["status"], "BLOCK_LANDED_COST_UNKNOWN")

    def test_unverified_cost_blocks(self):
        row = sample()
        row["unit_cost_verified"] = False
        self.assertEqual(audit_variant(row)["status"], "BLOCK_COST_EVIDENCE")

    def test_missing_rights_blocks(self):
        row = sample()
        row["rights_verified"] = False
        self.assertEqual(audit_variant(row)["status"], "BLOCK_RIGHTS")

    def test_missing_evidence_blocks(self):
        row = sample()
        row["evidence"] = {}
        self.assertEqual(audit_variant(row)["status"], "BLOCK_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
