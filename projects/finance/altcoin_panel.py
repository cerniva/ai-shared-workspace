"""Altcoin 10-indicator panel: raw data -> explicit methodology -> optional 0-100 score.

Data comes from a pluggable source returning daily closes and volumes
(oldest first). CoinGeckoSource uses the free, keyless public
/coins/{id}/market_chart endpoint; tests use FixtureSource. No API key is
read or needed.

Scores: each indicator has a raw value. A 0-100 bullish-support score is
produced only when a calibration (lo, hi, direction) is supplied for that
indicator AND marked validated; otherwise the score is "N/A". This module
ships no calibration, so out of the box every score is N/A by design (no
invented scores).
"""
from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Protocol


class Series(Protocol):
    def closes_volumes(self, coin: str, days: int) -> tuple[list[float], list[float]]: ...


@dataclass
class FixtureSource:
    data: dict[str, tuple[list[float], list[float]]]

    def closes_volumes(self, coin: str, days: int) -> tuple[list[float], list[float]]:
        closes, vols = self.data[coin]
        return closes[-days:], vols[-days:]


class CoinGeckoSource:
    """Free keyless public endpoint; rate-limited, no SLA. Daily granularity for days>90."""

    URL = "https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days={days}&interval=daily"

    def __init__(self, opener: Callable[..., Any] = urllib.request.urlopen):
        self.opener = opener

    def closes_volumes(self, coin: str, days: int) -> tuple[list[float], list[float]]:
        url = self.URL.format(coin=urllib.parse.quote(coin, safe=""), days=int(days))
        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "cerniva-finance-panel/1"})
        with self.opener(req, timeout=30) as resp:
            doc = json.loads(resp.read().decode("utf-8"))
        closes = [float(p[1]) for p in doc.get("prices", [])]
        vols = [float(p[1]) for p in doc.get("total_volumes", [])]
        if not closes or len(closes) != len(vols):
            raise ValueError(f"coingecko returned unusable series for {coin}")
        return closes, vols


def _sma(xs: list[float], n: int) -> float:
    return sum(xs[-n:]) / n


def _ret(xs: list[float], n: int) -> float:
    return xs[-1] / xs[-1 - n] - 1


def _rsi(xs: list[float], n: int = 14) -> float:
    diffs = [b - a for a, b in zip(xs[-n - 1:-1], xs[-n:])]
    gain = sum(d for d in diffs if d > 0) / n
    loss = -sum(d for d in diffs if d < 0) / n
    return 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)


def _vol(xs: list[float], n: int) -> float:
    rets = [math.log(b / a) for a, b in zip(xs[-n - 1:-1], xs[-n:])]
    m = sum(rets) / n
    return math.sqrt(sum((r - m) ** 2 for r in rets) / (n - 1)) * math.sqrt(365)


def _max_dd(xs: list[float]) -> float:
    peak, dd = xs[0], 0.0
    for x in xs:
        peak = max(peak, x)
        dd = min(dd, x / peak - 1)
    return dd


# name -> (definition, function(closes, volumes, btc_closes))
INDICATORS: dict[str, tuple[str, Callable[[list[float], list[float], list[float]], float]]] = {
    "return_7d": ("close/close[-7]-1", lambda c, v, b: _ret(c, 7)),
    "return_30d": ("close/close[-30]-1", lambda c, v, b: _ret(c, 30)),
    "price_vs_sma50": ("close/SMA50-1", lambda c, v, b: c[-1] / _sma(c, 50) - 1),
    "sma20_vs_sma50": ("SMA20/SMA50-1", lambda c, v, b: _sma(c, 20) / _sma(c, 50) - 1),
    "rsi14": ("Wilder-style simple-average RSI over 14 daily closes", lambda c, v, b: _rsi(c, 14)),
    "volatility_30d": ("annualized stdev of 30 daily log returns", lambda c, v, b: _vol(c, 30)),
    "volume_trend": ("mean volume 7d / mean volume 30d - 1", lambda c, v, b: _sma(v, 7) / _sma(v, 30) - 1),
    "max_drawdown_90d": ("worst peak-to-trough over 90 closes", lambda c, v, b: _max_dd(c[-90:])),
    "dist_from_90d_high": ("close/max(close[-90:])-1", lambda c, v, b: c[-1] / max(c[-90:]) - 1),
    "rel_strength_vs_btc_30d": ("return_30d(coin) - return_30d(BTC)", lambda c, v, b: _ret(c, 30) - _ret(b, 30)),
}
MIN_DAYS = 91


def score(value: float, calibration: dict[str, Any] | None) -> float | str:
    """Linear map to 0-100 only for a validated calibration, else 'N/A'."""
    if not calibration or not calibration.get("validated"):
        return "N/A"
    lo, hi = float(calibration["lo"]), float(calibration["hi"])
    if hi <= lo:
        return "N/A"
    frac = min(1.0, max(0.0, (value - lo) / (hi - lo)))
    if calibration.get("direction") == "lower_is_bullish":
        frac = 1 - frac
    return round(100 * frac, 1)


def panel(coin: str, source: Series, calibrations: dict[str, dict[str, Any]] | None = None,
          btc_id: str = "bitcoin") -> dict[str, Any]:
    closes, vols = source.closes_volumes(coin, MIN_DAYS)
    btc, _ = source.closes_volumes(btc_id, MIN_DAYS)
    if min(len(closes), len(vols), len(btc)) < MIN_DAYS:
        return {"coin": coin, "status": "INSUFFICIENT_DATA", "need_days": MIN_DAYS, "indicators": {}}
    calibrations = calibrations or {}
    rows = {}
    for name, (definition, fn) in INDICATORS.items():
        try:
            value = fn(closes, vols, btc)
        except (ZeroDivisionError, ValueError):
            value = float("nan")
        finite = math.isfinite(value)
        rows[name] = {"definition": definition, "value": round(value, 6) if finite else None,
                      "score": score(value, calibrations.get(name)) if finite else "N/A"}
    scored = [r["score"] for r in rows.values() if r["score"] != "N/A"]
    composite = round(sum(scored) / len(scored), 1) if len(scored) == len(rows) else "N/A"
    return {"coin": coin, "status": "OK", "days": MIN_DAYS, "indicators": rows, "composite_score": composite}


# --- Altseason regime panel (ChatGPT 9955ad3 indicator list) -------------------
# Indicators, sources and directions live in config/altcoin_panel_calibration.json.
# lo/hi come only from train-only p20/p80 of the preceding 730 daily values (or
# natural 0/100 bounds); a score is produced only for indicators marked validated.

from pathlib import Path as _Path

CALIBRATION_CONFIG = _Path(__file__).resolve().parents[2] / "config" / "altcoin_panel_calibration.json"


def load_calibration_config(path: _Path = CALIBRATION_CONFIG) -> dict[str, Any]:
    cfg = json.loads(_Path(path).read_text(encoding="utf-8"))
    names = [i["name"] for i in cfg["indicators"]]
    if cfg.get("schema_version") != 1 or len(names) != len(set(names)):
        raise ValueError("altcoin calibration config invalid")
    for ind in cfg["indicators"]:
        if ind["direction"] not in ("higher_is_bullish", "lower_is_bullish", "nonmonotonic"):
            raise ValueError(f"{ind['name']}: bad direction")
    return cfg


def _percentile(sorted_xs: list[float], pct: float) -> float:
    k = (len(sorted_xs) - 1) * pct / 100
    f = math.floor(k)
    c = min(f + 1, len(sorted_xs) - 1)
    return sorted_xs[f] + (sorted_xs[c] - sorted_xs[f]) * (k - f)


def fit_train_bounds(history: list[float | None], as_of: int, params: dict[str, Any]) -> tuple[float, float] | None:
    """p20/p80 over the train window strictly before index as_of; None if coverage too thin."""
    days = int(params["train_days"])
    if as_of < days:
        return None  # early fold without a full train window: no score
    window = history[as_of - days:as_of]
    valid = sorted(float(v) for v in window if v is not None and math.isfinite(float(v)))
    if len(valid) < int(params["min_valid_obs"]) or len(valid) / days < float(params["min_coverage"]):
        return None
    lo, hi = _percentile(valid, params["lo_pct"]), _percentile(valid, params["hi_pct"])
    return None if lo >= hi else (lo, hi)


FINANCE_ALTSEASON_LEARNING_ID = "learn_f7b141c60755c294"


def _require_altseason_learning(cfg: dict[str, Any]) -> str:
    """Fail closed unless the active, source-linked Finance policy matches the gate.

    This is called by the *decision producer*, not by a detached loader job.
    """
    from scripts.plan_learnings import plan_learnings
    from scripts.knowledge_bridge import CatalogError, SourceCatalog

    report = plan_learnings("finance")
    if report.get("error"):
        raise ValueError("bridge_failure: finance learning load failed: " + str(report["error"]))
    matches = [item for item in report.get("learnings", [])
               if item.get("learning_id") == FINANCE_ALTSEASON_LEARNING_ID]
    if len(matches) != 1:
        raise ValueError("bridge_failure: altseason learning missing or duplicate")
    row = matches[0]
    if not row.get("source_ids"):
        raise ValueError("bridge_failure: active, source-linked altseason learning missing")
    try:
        known_sources = {item["source_id"] for item in SourceCatalog().list()}
    except (CatalogError, OSError, ValueError, KeyError) as exc:
        raise ValueError("bridge_failure: finance source catalog unavailable") from exc
    if not set(row["source_ids"]).issubset(known_sources):
        raise ValueError("bridge_failure: altseason learning references unknown source_ids")
    decision = row.get("decision", "")
    if not all(token in decision for token in ("No invented 0-100 values", "p20", "p80", "730")):
        raise ValueError("bridge_failure: altseason learning policy changed; review gate")
    params = cfg.get("calibration") or {}
    expected = {"train_days": 730, "min_valid_obs": 500, "min_coverage": 0.8,
                "lo_pct": 20, "hi_pct": 80, "holdout_days": 90, "step_days": 90}
    if any(params.get(key) != value for key, value in expected.items()):
        raise ValueError("bridge_failure: calibration parameters differ from active learning")
    return FINANCE_ALTSEASON_LEARNING_ID


def altseason_panel(values: dict[str, float | None], cfg: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = cfg or load_calibration_config()
    applied_learning_id = _require_altseason_learning(cfg)
    rows = {}
    for ind in cfg["indicators"]:
        x = values.get(ind["name"])
        direction = ind["direction"]
        if x is None or direction == "nonmonotonic" or ind.get("lo") is None or ind.get("hi") is None:
            s: float | str = "N/A"
        else:
            s = score(float(x), {"lo": ind["lo"], "hi": ind["hi"], "validated": ind.get("validated", False),
                                 "direction": "lower_is_bullish" if direction == "lower_is_bullish" else "higher"})
        rows[ind["name"]] = {"value": x, "direction": direction, "source_url": ind["source_url"], "score": s}
    scored = [r["score"] for r in rows.values() if r["score"] != "N/A"]
    composite = round(sum(scored) / len(scored), 1) if scored and len(scored) == len(rows) else "N/A"
    return {"indicators": rows, "composite_score": composite, "scored": len(scored), "total": len(rows),
            "applied_learning_ids": [applied_learning_id]}
