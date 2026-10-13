#!/usr/bin/env python3
"""Read-only, fail-closed unit-economics screening for draft Shopify products.

Inputs must come from authorized store reads and independently verified cost,
shipping, fee, returns, rights and demand evidence. REVIEW_ONLY is never an
approval to publish, set prices, buy inventory, change payments or advertise.
"""
from __future__ import annotations

import argparse
import json
from decimal import Decimal, InvalidOperation
from pathlib import Path


def amount(value: object, field: str) -> Decimal:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field} missing or invalid")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field} invalid") from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f"{field} must be finite and nonnegative")
    return number


def audit_variant(row: dict) -> dict:
    """Fail closed on missing cost evidence; REVIEW_ONLY is not publish approval."""
    if not isinstance(row, dict):
        return {"status": "BLOCK_DATA", "reason": "variant must be an object"}
    if row.get("status") != "DRAFT":
        return {"status": "BLOCK_NOT_DRAFT", "reason": "read-only gate only screens draft products"}
    if row.get("cost_currency") != row.get("price_currency") or row.get("price_currency") != "EUR":
        return {"status": "BLOCK_CURRENCY", "reason": "cost and price require same verified EUR currency"}
    try:
        price = amount(row.get("price"), "price")
        unit_cost = amount(row.get("unit_cost"), "unit_cost")
    except ValueError as exc:
        return {"status": "BLOCK_DATA", "reason": str(exc)}
    spread = price - unit_cost
    if spread <= 0:
        return {"status": "BLOCK_NONPOSITIVE_SPREAD", "spread_eur": str(spread),
                "reason": "price <= unit cost before shipping and fees"}
    if row.get("unit_cost_verified") is not True:
        return {"status": "BLOCK_COST_EVIDENCE", "reason": "unit cost must be independently verified"}
    if row.get("rights_verified") is not True:
        return {"status": "BLOCK_RIGHTS", "reason": "product/asset rights not verified"}
    requires_shipping = row.get("requires_shipping")
    if not isinstance(requires_shipping, bool):
        return {"status": "BLOCK_DATA", "reason": "requires_shipping must be a boolean"}
    if requires_shipping:
        if row.get("weight_verified") is not True:
            return {"status": "BLOCK_WEIGHT", "reason": "packaged weight not independently verified", "spread_eur": str(spread)}
        try:
            weight = amount(row.get("weight_kg"), "weight_kg")
            if weight <= 0:
                raise ValueError("weight_kg must be positive")
        except ValueError as exc:
            return {"status": "BLOCK_WEIGHT", "reason": str(exc), "spread_eur": str(spread)}
    elif row.get("digital_delivery_verified") is not True:
        return {"status": "BLOCK_DELIVERY", "reason": "digital delivery file/link not verified", "spread_eur": str(spread)}
    try:
        shipping = amount(row.get("shipping_cost") if requires_shipping else 0, "shipping_cost")
        payment_fees = amount(row.get("payment_fees"), "payment_fees")
        return_reserve = amount(row.get("return_reserve"), "return_reserve")
        tax_reserve = amount(row.get("tax_reserve"), "tax_reserve")
    except ValueError as exc:
        return {"status": "BLOCK_LANDED_COST_UNKNOWN", "reason": str(exc), "spread_eur": str(spread)}
    contribution = spread - shipping - payment_fees - return_reserve - tax_reserve
    if contribution <= 0:
        return {"status": "BLOCK_NONPOSITIVE_CONTRIBUTION", "contribution_eur": str(contribution)}
    if row.get("demand_evidence_verified") is not True:
        return {"status": "REVIEW_DEMAND_UNVERIFIED", "contribution_eur": str(contribution),
                "note": "positive contribution does not prove demand or net profit"}
    evidence = row.get("evidence") or {}
    needed = ("unit_cost", "rights", "payment_fees", "returns", "taxes", "demand")
    needed += ("shipping", "weight") if requires_shipping else ("digital_delivery",)
    if not isinstance(evidence, dict) or any(
        not isinstance(evidence.get(key), str) or not evidence[key].strip()
        for key in needed
    ):
        missing = [key for key in needed if not isinstance(evidence.get(key), str) or not evidence[key].strip()]
        return {"status": "BLOCK_EVIDENCE", "reason": "missing independent provenance for: " + ", ".join(missing),
                "contribution_eur": str(contribution)}
    return {"status": "REVIEW_ONLY", "contribution_eur": str(contribution),
            "note": "not approval to publish, alter price, order, or advertise"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_path", type=Path)
    args = parser.parse_args()
    data = json.loads(args.json_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        parser.error("input must be a list of variant objects")
    print(json.dumps([audit_variant(row) for row in data], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
