# Keyless market data sources (verified 2026-10-10)

Replacements for blocked sources in config/altcoin_panel_calibration.json. Tested with curl from the
Grok Bot box (TR egress) and from GitHub Actions (US, via finans-dry-run workflow).

| Need | Working source (no key) | Notes |
|---|---|---|
| DXY | https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?range=5d&interval=1d | `chart.result[0].meta.regularMarketPrice`. Requires a browser-like User-Agent (no UA -> HTTP 429). Unofficial, no SLA. |
| VIX | https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv | Official CBOE daily OHLC since 1990, CLOSE = column 5. Follow redirects (307). |
| VIX (alt) | https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX | Same UA caveat. |
| VIX / broad USD (FRED) | https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS / DTWEXBGS | Intermittent: timed out once, 200 on retry. Use as backup with retries. DTWEXBGS is broad trade-weighted USD, not ICE DXY. |
| BTC funding | https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP | `data[0].fundingRate` |
| BTC OI | https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP ; history: /api/v5/rubik/stat/contracts/open-interest-volume?ccy=BTC&period=1D | `oiUsd` |
| Funding + OI (alt) | https://www.deribit.com/api/v2/public/get_book_summary_by_instrument?instrument_name=BTC-PERPETUAL | `funding_8h`, `open_interest` (USD) |
| Binance history | https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT/BTCUSDT-metrics-YYYY-MM-DD.zip | Daily OI/long-short metrics; S3 archive, not geo-blocked. |

Blocked / do not use:
- Stooq: JS browser-check page, not CSV.
- fapi.binance.com: HTTP 451 restricted location (also blocks US runners).
- api.bybit.com: HTTP 403 CloudFront country block from TR box (US also restricted by Bybit ToS).
