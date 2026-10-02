"""Validate finance report packets against the shared contract.

This module does not fetch prices, news, or render charts.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "projects" / "finance" / "report_contract.json"
FOOTER = "CHAT GPT ANALİZİ:"


def load_contract(path: Path | None = None) -> dict:
    target = path or CONTRACT_PATH
    data = json.loads(target.read_text(encoding="utf-8"))
    if data.get("python_chart_generation") is not False:
        raise ValueError("contract must keep python_chart_generation false")
    if data.get("live_market_generation") is not False:
        raise ValueError("contract must keep live_market_generation false")
    if data.get("report_footer_exact") != FOOTER:
        raise ValueError("contract footer drifted")
    return data


def validate_packet(packet: dict, contract: dict | None = None) -> list[str]:
    rules = contract or load_contract()
    errors: list[str] = []
    if not isinstance(packet, dict):
        return ["packet must be an object"]
    if packet.get("live_prices_invented") is True:
        errors.append("invented live prices are forbidden")
    if packet.get("python_chart_generated") is True or packet.get("chart_renderer") == "python":
        errors.append("python chart generation is forbidden")
    classes = packet.get("asset_classes")
    if not isinstance(classes, list) or not classes:
        errors.append("asset_classes must be a non-empty list")
    else:
        for name in rules.get("required_named_classes", []):
            if name not in classes:
                errors.append(f"missing required asset class: {name}")
    charts = packet.get("charts")
    if not isinstance(charts, list) or not charts:
        errors.append("charts must declare base-100 panels")
    else:
        metals = [c for c in charts if c.get("asset_class") == "metals"]
        crypto = [c for c in charts if c.get("asset_class") == "crypto"]
        if not metals or not crypto:
            errors.append("metals and crypto need separate chart entries")
        if any(c.get("asset_class") == "metals+crypto" for c in charts):
            errors.append("metals and crypto must not share a chart")
        for chart in charts:
            if chart.get("normalization") != "base-100":
                errors.append("chart missing base-100 normalization")
            if chart.get("index_base") != 100:
                errors.append("chart index_base must be 100")
            if chart.get("absolute_price_axis") is True:
                errors.append("absolute price axis is forbidden")
    panel = packet.get("altcoin_bull_panel")
    if not isinstance(panel, dict) or panel.get("normalized_panels") != 2:
        errors.append("altcoin bull panel requires two normalized panels")
    elif panel.get("normalization") != "base-100":
        errors.append("altcoin bull panel must be base-100 normalized")
    footer = packet.get("footer")
    if footer != rules.get("report_footer_exact"):
        errors.append("footer must be exactly CHAT GPT ANALİZİ:")
    sources = packet.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("verified sources are required")
    else:
        for source in sources:
            if not source.get("source_id"):
                errors.append("source missing catalog source_id")
            if source.get("provenance") != "verified":
                errors.append("source provenance must be verified")
            if source.get("price") is not None:
                errors.append("packet must not embed invented prices")
    return errors
