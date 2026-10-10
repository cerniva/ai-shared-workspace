#!/usr/bin/env python3
"""Hourly / event-triggered finance report -> messages/finance-report-latest.md.

Rules (HO finance report bot):
- Only free, keyless sources; every number and headline carries its source URL.
- Altcoin panel scores stay "N/A" unless config/altcoin_panel_calibration.json marks them validated.
- No investment advice. Moves are described, matching headlines are listed, no causal claims.
- Optional LLM summary goes ONLY through scripts.model_fallback; it is kept only if every
  line cites a URL that already appears in the collected data. Otherwise (or with no
  provider / FINANCE_REPORT_LLM!=1) the report is fully deterministic.
"""
from __future__ import annotations

import email.utils
import json
import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from projects.finance import altcoin_panel as ap  # noqa: E402

OUT_PATH = ROOT / "messages" / "finance-report-latest.md"
UA = {"User-Agent": "Mozilla/5.0 (cerniva-finance-report)", "Accept": "*/*"}
DISCLAIMER = "Yatırım tavsiyesi değildir. Bu rapor yalnızca kamuya açık verileri ve kaynak bağlantılarını derler."

Http = Callable[[str], bytes]


def default_http(url: str) -> bytes:
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        return r.read()


def _pct(now: float, prev: float | None) -> float | None:
    return None if not prev else (now / prev - 1) * 100


# ---------------------------------------------------------------- metrics
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range=5d&interval=1d"
CBOE_VIX = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"
CG_GLOBAL = "https://api.coingecko.com/api/v3/global"
OKX_ETHBTC = "https://www.okx.com/api/v5/market/ticker?instId=ETH-BTC"
LLAMA_STABLES = "https://stablecoins.llama.fi/stablecoins?includePrices=false"
OKX_FUNDING = "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP"
OKX_OI = "https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP"
DERIBIT = "https://www.deribit.com/api/v2/public/get_book_summary_by_instrument?instrument_name=BTC-PERPETUAL"


def m(key: str, label: str, value: float, url: str, unit: str = "", change: float | None = None,
      note: str = "") -> dict[str, Any]:
    return {"key": key, "label": label, "value": value, "unit": unit, "change_pct": change,
            "source_url": url, "note": note}


def fetch_yahoo(http: Http, sym: str, key: str, label: str) -> list[dict]:
    url = YAHOO.format(sym=sym)
    meta = json.loads(http(url))["chart"]["result"][0]["meta"]
    px = float(meta["regularMarketPrice"])
    return [m(key, label, px, url, change=_pct(px, meta.get("chartPreviousClose") or meta.get("previousClose")),
              note="değişim: 5 günlük grafiğin önceki kapanışına göre")]


def fetch_cboe_vix(http: Http) -> list[dict]:
    rows = [r.split(",") for r in http(CBOE_VIX).decode().strip().splitlines()]
    last, prev = rows[-1], rows[-2]
    return [m("vix_close", f"VIX resmi kapanış ({last[0]})", float(last[4]), CBOE_VIX,
              change=_pct(float(last[4]), float(prev[4])))]


def fetch_coingecko_global(http: Http) -> list[dict]:
    d = json.loads(http(CG_GLOBAL))["data"]
    total = float(d["total_market_cap"]["usd"])
    pct = d["market_cap_percentage"]
    btc, eth = float(pct["btc"]), float(pct["eth"])
    ch = d.get("market_cap_change_percentage_24h_usd")
    derived = "türetilmiş: toplam piyasa değeri × (1 − dominans payları); TradingView TOTAL2/3 ile birebir aynı değil"
    return [
        m("total_mcap", "Toplam kripto piyasa değeri", total, CG_GLOBAL, "USD", ch),
        m("btc_dominance", "BTC dominansı", btc, CG_GLOBAL, "%"),
        m("total2", "TOTAL2 (BTC hariç)", total * (1 - btc / 100), CG_GLOBAL, "USD", note=derived),
        m("total3", "TOTAL3 (BTC+ETH hariç)", total * (1 - (btc + eth) / 100), CG_GLOBAL, "USD", note=derived),
    ]


def fetch_ethbtc(http: Http) -> list[dict]:
    t = json.loads(http(OKX_ETHBTC))["data"][0]
    last = float(t["last"])
    return [m("eth_btc", "ETH/BTC", last, OKX_ETHBTC, "BTC", _pct(last, float(t["open24h"])),
              note="değişim: OKX 24s açılışa göre")]


def fetch_stablecoins(http: Http) -> list[dict]:
    assets = json.loads(http(LLAMA_STABLES))["peggedAssets"]

    def tot(field: str) -> float:
        return sum(float((a.get(field) or {}).get("peggedUSD") or 0) for a in assets)
    now, day, week = tot("circulating"), tot("circulatingPrevDay"), tot("circulatingPrevWeek")
    return [m("stablecoin_supply", "USD stablecoin arzı", now, LLAMA_STABLES, "USD", _pct(now, day),
              note=f"7g değişim: {_fmt_pct(_pct(now, week))}")]


def fetch_okx_derivs(http: Http) -> list[dict]:
    f = float(json.loads(http(OKX_FUNDING))["data"][0]["fundingRate"])
    oi = float(json.loads(http(OKX_OI))["data"][0]["oiUsd"])
    return [m("btc_funding_okx", "BTC-USDT perp fonlama (OKX, dönem)", f * 100, OKX_FUNDING, "%"),
            m("btc_oi_okx", "BTC-USDT perp açık pozisyon (OKX)", oi, OKX_OI, "USD")]


def fetch_deribit(http: Http) -> list[dict]:
    r = json.loads(http(DERIBIT))["result"][0]
    return [m("btc_funding_deribit", "BTC-PERPETUAL 8s fonlama (Deribit)", float(r["funding_8h"]) * 100, DERIBIT, "%"),
            m("btc_oi_deribit", "BTC-PERPETUAL açık pozisyon (Deribit)", float(r["open_interest"]), DERIBIT, "USD")]


METRIC_FETCHERS: dict[str, Callable[[Http], list[dict]]] = {
    "yahoo_dxy": lambda h: fetch_yahoo(h, "DX-Y.NYB", "dxy", "DXY (ICE ABD doları endeksi)"),
    "yahoo_vix": lambda h: fetch_yahoo(h, "%5EVIX", "vix", "VIX"),
    "cboe_vix": fetch_cboe_vix,
    "coingecko_global": fetch_coingecko_global,
    "okx_ethbtc": fetch_ethbtc,
    "defillama_stablecoins": fetch_stablecoins,
    "okx_derivatives": fetch_okx_derivs,
    "deribit": fetch_deribit,
}

# ---------------------------------------------------------------- news / decisions
FEEDS = {
    "fed": ("Fed basın açıklamaları (para politikası)", "https://www.federalreserve.gov/feeds/press_monetary.xml"),
    "tcmb_ppk": ("TCMB PPK kararları", "https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB+EN/Bottom+Menu/Other/RSS/MPC+Decisions"),
    "tcmb_press": ("TCMB basın duyuruları", "https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB+EN/Bottom+Menu/Other/RSS/Press+Releases"),
    "bbc_business": ("Ekonomi haberleri (BBC Business)", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    "bbc_world": ("Siyasi gelişmeler / olaylar (BBC World)", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    "coindesk": ("Kripto haberleri (CoinDesk)", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
    "cointelegraph": ("Kripto haberleri (Cointelegraph)", "https://cointelegraph.com/rss"),
}
ATOM = "{http://www.w3.org/2005/Atom}"


def parse_feed(raw: bytes, limit: int = 5) -> list[dict[str, str]]:
    root = ET.fromstring(raw.strip())
    items = []
    for it in root.iter("item"):
        items.append({"title": (it.findtext("title") or "").strip(), "link": (it.findtext("link") or "").strip(),
                      "published": (it.findtext("pubDate") or "").strip()})
    for e in root.iter(f"{ATOM}entry"):
        link = e.find(f"{ATOM}link")
        items.append({"title": (e.findtext(f"{ATOM}title") or "").strip(),
                      "link": (link.get("href") if link is not None else "").strip(),
                      "published": (e.findtext(f"{ATOM}updated") or e.findtext(f"{ATOM}published") or "").strip()})
    return [i for i in items if i["title"] and i["link"].startswith("http")][:limit]


# ---------------------------------------------------------------- collect
def collect(http: Http = default_http) -> dict[str, Any]:
    metrics, errors, news = [], {}, {}
    for name, fn in METRIC_FETCHERS.items():
        try:
            metrics.extend(fn(http))
        except Exception as e:  # noqa: BLE001 - report, never crash
            errors[name] = f"{type(e).__name__}: {e}"[:160]
    for key, (label, url) in FEEDS.items():
        try:
            news[key] = {"label": label, "url": url, "items": parse_feed(http(url))}
        except Exception as e:  # noqa: BLE001
            errors[key] = f"{type(e).__name__}: {e}"[:160]
    return {"metrics": metrics, "news": news, "errors": errors}


def panel_values(metrics: list[dict]) -> dict[str, float]:
    by = {x["key"]: x["value"] for x in metrics}
    out = {}
    for src, dst in (("btc_dominance", "btc_dominance"), ("eth_btc", "eth_btc"), ("dxy", "dxy"), ("vix", "vix")):
        if src in by:
            out[dst] = by[src]
    if "vix" not in out and "vix_close" in by:
        out["vix"] = by["vix_close"]
    return out


# ---------------------------------------------------------------- render
def _fmt_num(v: float, unit: str) -> str:
    if unit == "USD" and abs(v) >= 1e9:
        return f"${v / 1e9:,.2f} mlr"
    if unit == "USD" and abs(v) >= 1e6:
        return f"${v / 1e6:,.1f} mn"
    if unit == "%":
        return f"%{v:.4f}" if abs(v) < 1 else f"%{v:.2f}"
    if unit == "BTC":
        return f"{v:.5f} BTC"
    return f"{v:,.2f}"


def _fmt_pct(p: float | None) -> str:
    return "—" if p is None else f"{p:+.2f}%"


MOVE_KEYWORDS = {
    "dxy": r"\bfed\b|fomc|interest rate|inflation|dollar|tariff|treasury|yield|\bcpi\b|payrolls",
    "vix": r"stock|market|sell-?off|war|tariff|recession|volatil",
    "total_mcap": r"bitcoin|crypto|btc|ether|etf|stablecoin|sec\b",
}


def parse_date(text: str) -> datetime | None:
    text = (text or "").strip()
    try:
        d = email.utils.parsedate_to_datetime(text)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    for fmt in ("%b %d, %Y, %I:%M:%S %p", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            d = datetime.strptime(text, fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


RECENT = timedelta(hours=48)


def explain_moves(data: dict, now: datetime) -> list[str]:
    lines = []
    all_news = [i for f in data["news"].values() for i in f["items"]
                if (d := parse_date(i["published"])) is not None and now - RECENT <= d <= now + timedelta(hours=1)]
    for x in data["metrics"]:
        pattern = MOVE_KEYWORDS.get(x["key"])
        if not pattern or x["change_pct"] is None:
            continue
        hits = [i for i in all_news if re.search(pattern, i["title"], re.I)][:3]
        yön = "yükseldi" if x["change_pct"] > 0 else "düştü" if x["change_pct"] < 0 else "yatay"
        lines.append(f"- **{x['label']}** {_fmt_pct(x['change_pct'])} {yön} ([kaynak]({x['source_url']})).")
        if hits:
            lines.append("  - Aynı dönemde ilgili başlıklar (nedensellik iddiası değildir): "
                         + "; ".join(f"[{h['title']}]({h['link']})" for h in hits))
        else:
            lines.append("  - Son 48 saatte eşleşen başlık bulunamadı; açıklama yapılmadı.")
    return lines or ["- Değişim verisi alınamadı."]


def render(data: dict[str, Any], now: datetime, panel: dict[str, Any], summary: str | None = None) -> str:
    L = [f"# Finans raporu — {now.strftime('%Y-%m-%d %H:%M')} UTC", "", f"> {DISCLAIMER}", ""]
    if summary:
        L += ["## Model özeti (kaynak kontrolünden geçti)", "", summary.strip(), ""]
    L += ["## Piyasa hareketleri", ""] + explain_moves(data, now) + [""]
    L += ["## Göstergeler", "", "| Gösterge | Değer | Değişim | Kaynak | Not |", "|---|---|---|---|---|"]
    for x in data["metrics"]:
        L.append(f"| {x['label']} | {_fmt_num(x['value'], x['unit'])} | {_fmt_pct(x['change_pct'])} | "
                 f"[link]({x['source_url']}) | {x['note']} |")
    L += ["", "## Altcoin boğa paneli (kalibrasyon yok → skorlar N/A)", "",
          "| Gösterge | Değer | Yön | Skor | Kaynak |", "|---|---|---|---|---|"]
    for name, r in panel["indicators"].items():
        v = "—" if r["value"] is None else f"{r['value']:.6g}"
        L.append(f"| {name} | {v} | {r['direction']} | {r['score']} | [link]({r['source_url']}) |")
    L += ["", f"Bileşik skor: **{panel['composite_score']}** ({panel['scored']}/{panel['total']} skorlu)", ""]
    for key in ("fed", "tcmb_ppk", "tcmb_press", "bbc_business", "bbc_world", "coindesk", "cointelegraph"):
        f = data["news"].get(key)
        if not f:
            continue
        L += [f"## {f['label']}", f"Akış: {f['url']}", ""]
        dates = [d for i in f["items"] if (d := parse_date(i["published"])) is not None]
        if dates and max(dates) < now - timedelta(days=60):
            L += [f"_Uyarı: akıştaki en yeni öğe {max(dates).date()} tarihli; akış güncel olmayabilir._", ""]
        L += [f"- [{i['title']}]({i['link']})" + (f" — {i['published']}" if i["published"] else "") for i in f["items"]]
        L.append("")
    if data["errors"]:
        L += ["## Ulaşılamayan kaynaklar", ""] + [f"- {k}: {v}" for k, v in sorted(data["errors"].items())] + [""]
    return "\n".join(L).rstrip() + "\n"


# ---------------------------------------------------------------- optional LLM (model_fallback only)
URL_RE = re.compile(r"https?://[^\s)\]]+")


def known_urls(data: dict) -> set[str]:
    urls = {x["source_url"] for x in data["metrics"]}
    for f in data["news"].values():
        urls.add(f["url"])
        urls.update(i["link"] for i in f["items"])
    return urls


def validate_summary(text: str, allowed: set[str]) -> str | None:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if not lines or len(lines) > 8:
        return None
    for ln in lines:
        urls = URL_RE.findall(ln)
        if not urls or any(u not in allowed for u in urls):
            return None
        if re.search(r"\b(al|sat|buy|sell|tavsiye|recommend)\b", ln, re.I):
            return None
    return "\n".join(lines)


def llm_summary(data: dict, *, env=None, adapter_factory=None) -> str | None:
    env = os.environ if env is None else env
    if env.get("FINANCE_REPORT_LLM") != "1":
        return None
    try:
        if adapter_factory is None:
            from scripts.model_fallback import fallback_adapter as adapter_factory
        adapter = adapter_factory(env=env)
        if adapter is None:
            return None
        facts = json.dumps({"metrics": data["metrics"],
                            "news": {k: v["items"] for k, v in data["news"].items()}}, ensure_ascii=False)[:6000]
        job = {"id": "finance-report-" + datetime.now(timezone.utc).strftime("%Y%m%d%H"),
               "project": "finance-report", "simple": True, "evidence_requirements": [],
               "objective": "Aşağıdaki verilerden en fazla 5 madde Türkçe özet yaz. Her madde yalnızca verideki "
                            "bir URL'yi parantez içinde kaynak olarak göstermeli. Yatırım tavsiyesi verme, "
                            "veride olmayan bilgi ekleme. 'recommendation' alanına yaz.\n\n" + facts}
        return validate_summary(str(adapter.run(job).get("recommendation") or ""), known_urls(data))
    except Exception:  # noqa: BLE001 - CannotDo or provider errors -> deterministic report
        return None


def build(http: Http = default_http, *, now: datetime | None = None, env=None, adapter_factory=None) -> str:
    now = now or datetime.now(timezone.utc)
    data = collect(http)
    panel = ap.altseason_panel(panel_values(data["metrics"]), ap.load_calibration_config())
    return render(data, now, panel, llm_summary(data, env=env, adapter_factory=adapter_factory))


def main(argv: list[str] | None = None) -> int:
    out = Path((argv or sys.argv[1:] or [str(OUT_PATH)])[0])
    text = build()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
