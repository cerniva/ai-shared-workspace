# Video / Shopify audit — 2026-10-19 17:33 Europe/Istanbul

Status: CONTINUE; no publish, paid credits, video rendering, TTS, store changes or merge.

## Evidence read
- PROTOCOL.md, research/KNOWLEDGE_LEDGER.md, messages/team-reports.md, messages/grok-to-chatgpt.md, state/now.json.
- scripts/shorts_weekly_learning.py (main blob ffdf506d8d9a41a7900eceb004526f48fddcf075).
- tests/test_shorts_weekly_learning.py and knowledge/shorts/learnings/weekly-2026-43.json.
- Shopify connected store i19cci-4e.myshopify.com: 9 products all DRAFT; ShopifyQL sessions 2026-10-12 through 2026-10-19: zero sessions, cart additions, checkouts and completed checkouts.

## Metric defect and safe recommendation
- weekly-2026-43.json has channel views 5600, engaged_views 0, stayed_to_watch_percent 0; one per-video stayed_to_watch_percent 121.7. Treat zero as unverified when other engagement data is missing; 121.7 is invalid for swipe rate and may be a different metric.
- shorts_weekly_learning.py currently derives 9.7*3600/5600 ~ 6.2 seconds and calls it average watched per view. This ratio is NOT YouTube Shorts' official average view duration (official denominator uses engaged views and corresponding watch time). Do not generate hook/retention/length advice from it.
- Proposed guarded behavior: reject out-of-range swipe percentages, flag ambiguous zero values, label ratio as non-comparable or omit it; add regression tests. A source update was attempted on this isolated branch but blocked by connector safety checks; do not claim code fixed or tests passed.
- Sources: https://support.google.com/youtube/answer/12220281 and https://support.google.com/youtube/answer/1311392 .

## Video policy
- Current user instruction overrides older auto-publish/render SOP: existing food/entertainment footage only, verified commercial adaptation rights including audio, original audio preserved, same-language captions, observed 30–40s segment, no invented timestamps. No approved new video clip this run.
- Free manual editing candidate: https://www.capcut.com/tools/mp4-editor-online ; check free-tier features before use.
- Reused-content monetization risk remains even if copyright permission exists.

## Shopify gate
- Draft products and zero sessions do not establish lack of demand. Verify supplier landed costs, actual shipping countries/costs, returns, IP, customer trust and payment flow before any listing or ad.
- No product, price, ad, payment, or publication changes performed.

## Constraints
- PayoutLens excluded. Branch only; main unchanged. No secrets, paid services, merges or uploads.
