"""Validation gates added 2026-10-04 from official docs.

Preserves existing pool rules (storyboard-retention map, engagedViews/AVD/APV,
dip/spike uncertainty, analytics maturity, inventory/ETA/shipping). Does not
touch PayoutLens. Community benchmark bands are not pass/fail.
"""

from __future__ import annotations

US = "US"
EU = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR",
    "HU", "IS", "IE", "IT", "LV", "LI", "LT", "LU", "MT", "NL", "NO", "PL",
    "PT", "RO", "SK", "SI", "ES", "SE", "CH", "GB", "UK",
}


def validate_average_view_metrics(metrics: dict) -> dict:
    """AVD and APV exclude looping-clips traffic as of 2021-12-13.

    Official: https://developers.google.com/youtube/analytics/metrics
    A value above 100 on averageViewPercentage is not proof of loops in this
    metric. Missing values stay unknown; they are not a content failure.
    """
    avd = metrics.get("averageViewDuration")
    apv = metrics.get("averageViewPercentage")
    reasons = []
    if avd is None or apv is None:
        return {
            "gate": "LOOP_EXCLUDED_AVD_GATE",
            "status": "unknown",
            "reason": "averageViewDuration or averageViewPercentage missing",
            "loops_included": False,
        }
    if not isinstance(avd, (int, float)) or avd < 0:
        reasons.append("averageViewDuration must be a non-negative number of seconds")
    if not isinstance(apv, (int, float)) or apv < 0:
        reasons.append("averageViewPercentage must be a non-negative percentage")
    if apv is not None and apv > 100:
        reasons.append(
            "averageViewPercentage above 100 is not loop evidence; this metric excludes looping clips"
        )
    return {
        "gate": "LOOP_EXCLUDED_AVD_GATE",
        "status": "reject" if reasons else "accept",
        "reason": "; ".join(reasons) if reasons else "loops excluded; values kept as reported",
        "loops_included": False,
    }


def validate_retention_query(video_ids: list[str], audience_type: str | None = None) -> dict:
    """Retention reports are one video at a time.

    Official: https://developers.google.com/youtube/analytics/sample-requests
    audienceType==ORGANIC excludes TrueView ad views. Omitting it is allowed
    and means all audience types, not a failure.
    """
    ids = [v for v in video_ids if v]
    if len(ids) != 1:
        return {
            "gate": "SINGLE_VIDEO_RETENTION_QUERY_GATE",
            "status": "reject",
            "reason": "audience retention supports exactly one video filter value",
        }
    organic_only = audience_type == "ORGANIC"
    return {
        "gate": "SINGLE_VIDEO_RETENTION_QUERY_GATE",
        "status": "accept",
        "reason": "single video filter",
        "organic_only": organic_only,
        "ad_views_included": not organic_only,
    }


def validate_inventory_available(available) -> dict:
    """REST InventoryLevel.available is null when the item is not tracked.

    Official: https://shopify.dev/docs/api/admin-rest/latest/resources/inventorylevel
    Null must not be coerced to zero.
    """
    if available is None:
        return {
            "gate": "UNTRACKED_INVENTORY_NULL_GATE",
            "status": "unknown",
            "sellable": None,
            "reason": "available is null; inventory is not tracked",
        }
    if isinstance(available, bool) or not isinstance(available, int):
        return {
            "gate": "UNTRACKED_INVENTORY_NULL_GATE",
            "status": "reject",
            "sellable": None,
            "reason": "available must be an integer or null",
        }
    return {
        "gate": "UNTRACKED_INVENTORY_NULL_GATE",
        "status": "accept",
        "sellable": available,
        "reason": "tracked available quantity; incoming is still not included",
    }


def _region(code: str | None) -> str | None:
    if not code:
        return None
    c = code.upper()
    if c == "UK":
        c = "GB"
    if c == "US":
        return US
    if c in EU:
        return "EU"
    return None


def validate_automated_delivery_date(order: dict) -> dict:
    """Automated delivery date is shown only for eligible in-stock same-region orders.

    Official: https://help.shopify.com/en/manual/fulfillment/setup/delivery-expectations/automated-delivery-dates
    Over-window predictions fall back to manual dates, they are not automated dates.
    """
    origin = _region(order.get("origin_country"))
    dest = _region(order.get("destination_country"))
    days = order.get("prediction_days")
    reasons = []
    if origin is None or dest is None or origin != dest:
        reasons.append("origin and destination must be the same supported region")
    if not order.get("in_stock") or not order.get("immediate_fulfillment"):
        reasons.append("products must be in stock and immediately fulfillable")
    if not isinstance(days, (int, float)):
        reasons.append("prediction_days required")
    else:
        limit = 5 if origin == US else 4
        if origin in {US, "EU"} and days > limit:
            return {
                "gate": "AUTOMATED_DELIVERY_DATE_GATE",
                "status": "manual_fallback",
                "reason": f"prediction {days}d exceeds {limit}d automated window",
            }
    if reasons:
        return {
            "gate": "AUTOMATED_DELIVERY_DATE_GATE",
            "status": "reject",
            "reason": "; ".join(reasons),
        }
    return {
        "gate": "AUTOMATED_DELIVERY_DATE_GATE",
        "status": "accept",
        "reason": "eligible for automated delivery date",
    }


def validate_market_shipping_rates(rates: list[dict]) -> dict:
    """From 2026-10-01, multiple rates in one shipping option do not sum.

    Source: https://www.shopify.com/blog/fulfillment-on-shopify-2026
    Only the highest matching rate applies. Do not invent a store rate.
    """
    if not rates:
        return {
            "gate": "MARKET_RATE_HIGHEST_ONLY_GATE",
            "status": "unknown",
            "amount": None,
            "reason": "no matching rate",
        }
    amounts = []
    for rate in rates:
        amount = rate.get("amount")
        if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount < 0:
            return {
                "gate": "MARKET_RATE_HIGHEST_ONLY_GATE",
                "status": "reject",
                "amount": None,
                "reason": "rate amount must be a non-negative number",
            }
        amounts.append(amount)
    return {
        "gate": "MARKET_RATE_HIGHEST_ONLY_GATE",
        "status": "accept",
        "amount": max(amounts),
        "summed": False,
        "reason": "highest matching rate only",
    }
