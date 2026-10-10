"""Finance report bot: offline tests with fixture HTTP (no network)."""
from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

from scripts import finance_report as fr
from scripts import telegram_bot as tb

NOW = datetime(2026, 10, 10, 1, 0, tzinfo=timezone.utc)
RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel>
<item><title>Fed holds interest rate steady</title><link>https://www.federalreserve.gov/x.htm</link>
<pubDate>Fri, 09 Oct 2026 18:00:00 GMT</pubDate></item>
<item><title>Bitcoin ETF flows rise</title><link>https://news.example/btc</link>
<pubDate>Fri, 09 Oct 2026 20:00:00 GMT</pubDate></item></channel></rss>"""
ATOM = b"""<?xml version="1.0" encoding="utf-8"?><feed xmlns="http://www.w3.org/2005/Atom">
<entry><title type="text"><![CDATA[Press Release on Interest Rates (2025-61)]]></title>
<link rel="alternate" type="text/html" href="http://www.tcmb.gov.tr/a"></link>
<updated>Dec 11, 2025, 2:00:00 PM</updated></entry></feed>"""
FIXTURES = {
    fr.YAHOO.format(sym="DX-Y.NYB"): {"chart": {"result": [{"meta": {"regularMarketPrice": 102.0, "chartPreviousClose": 100.0}}]}},
    fr.YAHOO.format(sym="%5EVIX"): {"chart": {"result": [{"meta": {"regularMarketPrice": 15.0, "chartPreviousClose": 16.0}}]}},
    fr.CG_GLOBAL: {"data": {"total_market_cap": {"usd": 3e12}, "market_cap_percentage": {"btc": 60.0, "eth": 10.0},
                            "market_cap_change_percentage_24h_usd": -1.5}},
    fr.OKX_ETHBTC: {"data": [{"last": "0.03", "open24h": "0.031"}]},
    fr.LLAMA_STABLES: {"peggedAssets": [{"circulating": {"peggedUSD": 300e9}, "circulatingPrevDay": {"peggedUSD": 299e9},
                                         "circulatingPrevWeek": {"peggedUSD": 298e9}}]},
    fr.OKX_FUNDING: {"data": [{"fundingRate": "0.0001"}]},
    fr.OKX_OI: {"data": [{"oiUsd": "2500000000"}]},
    fr.DERIBIT: {"result": [{"funding_8h": 0.00002, "open_interest": 830000000}]},
}


def fake_http(url: str) -> bytes:
    if url in FIXTURES:
        return json.dumps(FIXTURES[url]).encode()
    if url == fr.CBOE_VIX:
        return b"DATE,OPEN,HIGH,LOW,CLOSE\n10/07/2026,1,1,1,15.08\n10/08/2026,1,1,1,15.41\n"
    if "tcmb" in url:
        return ATOM
    return RSS


def broken_http(url: str) -> bytes:
    raise OSError("blocked")


class FinanceReportTests(unittest.TestCase):
    def setUp(self):
        self.data = fr.collect(fake_http)

    def test_all_sources_collected_without_errors(self):
        self.assertEqual(self.data["errors"], {})
        keys = {x["key"] for x in self.data["metrics"]}
        for k in ("dxy", "vix", "vix_close", "btc_dominance", "total2", "total3", "eth_btc",
                  "stablecoin_supply", "btc_funding_okx", "btc_oi_okx", "btc_oi_deribit"):
            self.assertIn(k, keys)

    def test_every_metric_and_headline_has_source_url(self):
        for x in self.data["metrics"]:
            self.assertTrue(x["source_url"].startswith("https://"), x)
        for f in self.data["news"].values():
            for i in f["items"]:
                self.assertTrue(i["link"].startswith("http"))

    def test_total2_total3_derived(self):
        by = {x["key"]: x["value"] for x in self.data["metrics"]}
        self.assertAlmostEqual(by["total2"], 1.2e12, delta=1)
        self.assertAlmostEqual(by["total3"], 0.9e12, delta=1)

    def test_report_uncalibrated_scores_na_and_disclaimer(self):
        text = fr.build(fake_http, now=NOW, env={})
        self.assertIn(fr.DISCLAIMER, text)
        self.assertIn("Bileşik skor: **N/A**", text)
        self.assertNotRegex(text, r"\| (higher|lower)_is_bullish \| \d")
        self.assertIn("+2.00%", text)  # DXY 100 -> 102
        self.assertIn("[Fed holds interest rate steady](https://www.federalreserve.gov/x.htm)", text)
        self.assertIn("akış güncel olmayabilir", text)  # stale TCMB MPC feed flagged

    def test_blocked_sources_reported_not_crashing(self):
        text = fr.build(broken_http, now=NOW, env={})
        self.assertIn("Ulaşılamayan kaynaklar", text)
        self.assertIn("Bileşik skor: **N/A**", text)

    def test_llm_disabled_by_default_and_never_called(self):
        factory = mock.Mock()
        self.assertIsNone(fr.llm_summary(self.data, env={}, adapter_factory=factory))
        factory.assert_not_called()

    def test_llm_summary_kept_only_with_known_urls(self):
        good = "- DXY yükseldi (https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?range=5d&interval=1d)"
        adapter = mock.Mock()
        adapter.run.return_value = {"recommendation": good}
        out = fr.llm_summary(self.data, env={"FINANCE_REPORT_LLM": "1"}, adapter_factory=lambda env: adapter)
        self.assertEqual(out, good)
        adapter.run.return_value = {"recommendation": "- BTC 200k olacak (https://evil.example/x)"}
        self.assertIsNone(fr.llm_summary(self.data, env={"FINANCE_REPORT_LLM": "1"}, adapter_factory=lambda env: adapter))
        adapter.run.return_value = {"recommendation": "- Uncited claim"}
        self.assertIsNone(fr.llm_summary(self.data, env={"FINANCE_REPORT_LLM": "1"}, adapter_factory=lambda env: adapter))

    def test_llm_cannotdo_falls_back(self):
        from scripts.model_fallback import CannotDo
        adapter = mock.Mock()
        adapter.run.side_effect = CannotDo("YAPAMADIM")
        self.assertIsNone(fr.llm_summary(self.data, env={"FINANCE_REPORT_LLM": "1"}, adapter_factory=lambda env: adapter))
        self.assertIsNone(fr.llm_summary(self.data, env={"FINANCE_REPORT_LLM": "1"}, adapter_factory=lambda env: None))

    def test_advice_words_rejected(self):
        url = fr.CG_GLOBAL
        self.assertIsNone(fr.validate_summary(f"- Şimdi al ({url})", {url}))

    def test_main_writes_file(self):
        with tempfile.TemporaryDirectory() as d, mock.patch.object(fr, "default_http", fake_http):
            out = Path(d) / "r.md"
            with mock.patch.object(fr, "build", lambda: fr.render(fr.collect(fake_http), NOW,
                                   fr.ap.altseason_panel({}, fr.ap.load_calibration_config()))):
                self.assertEqual(fr.main([str(out)]), 0)
            self.assertTrue(out.read_text(encoding="utf-8").startswith("# Finans raporu"))


class DurumCommandTests(unittest.TestCase):
    def test_durum_returns_finance_report(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "finance-report-latest.md"
            p.write_text("# Finans raporu — test\nDXY 102", encoding="utf-8")
            with mock.patch.object(tb, "FINANCE_REPORT", p):
                factory = mock.Mock()
                self.assertEqual(tb.handle_text("/durum", adapter_factory=factory), "# Finans raporu — test\nDXY 102")
                factory.assert_not_called()

    def test_durum_truncates_long_report(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "r.md"
            p.write_text("x" * 10000, encoding="utf-8")
            out = tb.finance_report_text(p)
            self.assertLessEqual(len(out), tb.MAX_REPLY)
            self.assertIn("kısaltıldı", out)

    def test_durum_missing_report_falls_back(self):
        with mock.patch.object(tb, "FINANCE_REPORT", Path("/nonexistent/x.md")):
            self.assertEqual(tb.finance_report_text(), "")


if __name__ == "__main__":
    unittest.main()
