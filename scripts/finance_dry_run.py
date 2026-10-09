"""Finance pipeline dry-run: no secrets, no posting, no repo writes.

Probes the verified keyless sources for DXY / VIX / funding / OI, feeds what
it gets into the altseason panel (scores stay N/A until calibration is
validated) and prints a JSON summary. Network failures are reported, not
fatal: exit code is non-zero only if the config or panel code is broken.
"""
from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from projects.finance import altcoin_panel as ap  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (cerniva-finance-dry-run)"}


def get(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return r.read()


def yahoo(sym: str) -> float:
    d = json.loads(get(f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"))
    return float(d["chart"]["result"][0]["meta"]["regularMarketPrice"])


def cboe_vix() -> float:
    rows = list(csv.reader(io.StringIO(get("https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv").decode())))
    return float(rows[-1][4])


def okx_funding() -> float:
    d = json.loads(get("https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP"))
    return float(d["data"][0]["fundingRate"])


def okx_oi_usd() -> float:
    d = json.loads(get("https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP"))
    return float(d["data"][0]["oiUsd"])


def deribit_perp() -> dict:
    d = json.loads(get("https://www.deribit.com/api/v2/public/get_book_summary_by_instrument?instrument_name=BTC-PERPETUAL"))
    r = d["result"][0]
    return {"funding_8h": r.get("funding_8h"), "open_interest_usd": r.get("open_interest")}


PROBES = {
    "dxy_yahoo": lambda: yahoo("DX-Y.NYB"),
    "vix_yahoo": lambda: yahoo("%5EVIX"),
    "vix_cboe_csv": cboe_vix,
    "btc_funding_okx": okx_funding,
    "btc_oi_usd_okx": okx_oi_usd,
    "btc_perp_deribit": deribit_perp,
}


def main() -> int:
    cfg = ap.load_calibration_config()
    probes = {}
    for name, fn in PROBES.items():
        t = time.monotonic()
        try:
            probes[name] = {"ok": True, "value": fn()}
        except Exception as e:  # report, do not fail the dry run on network
            probes[name] = {"ok": False, "error": f"{type(e).__name__}: {e}"[:200]}
        probes[name]["ms"] = round((time.monotonic() - t) * 1000)
    values = {
        "dxy": probes["dxy_yahoo"].get("value"),
        "vix": probes["vix_yahoo"].get("value") or probes["vix_cboe_csv"].get("value"),
    }
    result = ap.altseason_panel(values, cfg)
    out = {"mode": "dry-run", "posting": "disabled", "probes": probes, "panel": result}
    print(json.dumps(out, indent=2, default=str))
    if result["total"] != len(cfg["indicators"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
