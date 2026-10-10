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

## Added for finance-report bot (verified 2026-10-10 ~01:00 UTC, box)

| Need | Source | Notes |
|---|---|---|
| BTC dominance, total mcap, TOTAL2/TOTAL3 (derived) | https://api.coingecko.com/api/v3/global | `market_cap_percentage.btc/eth`; TOTAL2/3 = total × (1 − shares), approximate vs TradingView. Rate-limited, no SLA. |
| ETH/BTC | https://www.okx.com/api/v5/market/ticker?instId=ETH-BTC | `last`, `open24h`. Yahoo `ETH-BTC` chart also works. |
| Stablecoin supply | https://stablecoins.llama.fi/stablecoins?includePrices=false | sum `circulating.peggedUSD` (+ PrevDay/PrevWeek). History: /stablecoincharts/all |
| Fed decisions | https://www.federalreserve.gov/feeds/press_monetary.xml | RSS 2.0 |
| TCMB MPC decisions | https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB+EN/Bottom+Menu/Other/RSS/MPC+Decisions | Atom; newest entry seen was 2025-12-11 → appears stale, report flags it |
| TCMB press releases | https://www.tcmb.gov.tr/wps/wcm/connect/EN/TCMB+EN/Bottom+Menu/Other/RSS/Press+Releases | Atom; current (2026-44 on 2026-10-09) |
| Economic / political news | https://feeds.bbci.co.uk/news/business/rss.xml , https://feeds.bbci.co.uk/news/world/rss.xml | RSS |
| Crypto news | https://www.coindesk.com/arc/outboundfeeds/rss/ , https://cointelegraph.com/rss | RSS |
| GDELT DOC API | https://api.gdeltproject.org/api/v2/doc/doc | NOT used: HTTP 429 after 12 s ("one request every 5 seconds") |
