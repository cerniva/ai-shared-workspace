# Retention and Shopify validation gates — 2026-10-04

Mail subject: [Task Update] Video ve Shopify Otomasyonu: Yeni retention ve Shopify doğrulama kuralları
Mail body was truncated after "İNTERNETTEN YENİ...". Existing pool rules were kept, not rewritten.

Preserved, not replaced:
- storyboard to retention mapping
- engagedViews / AVD / APV distinction
- dip/spike uncertainty
- analytics maturity window
- Shopify inventory / ETA / shipping, including INCOMING_ETA_GATE

New gates from public pages read 2026-10-04:

1. LOOP_EXCLUDED_AVD_GATE
   averageViewDuration and averageViewPercentage exclude looping-clips traffic as of 2021-12-13.
   Source: https://developers.google.com/youtube/analytics/metrics
   APV above 100 is not loop evidence for these metrics. Missing values stay unknown.

2. SINGLE_VIDEO_RETENTION_QUERY_GATE
   Audience retention can be retrieved for one video at a time. Multiple video filter values are unsupported.
   audienceType==ORGANIC excludes TrueView ad views; omitting it means all audience types.
   Source: https://developers.google.com/youtube/analytics/sample-requests

3. UNTRACKED_INVENTORY_NULL_GATE
   REST InventoryLevel.available is null when the item is not tracked. Do not coerce null to 0.
   Incoming remains excluded from available.
   Source: https://shopify.dev/docs/api/admin-rest/latest/resources/inventorylevel

4. AUTOMATED_DELIVERY_DATE_GATE
   Automated date only if in stock, immediately fulfillable, same supported region, and prediction within 5 days (US) or 4 days (Europe). Cross-region US/EU is not shown. Over-window falls back to manual dates.
   Source: https://help.shopify.com/en/manual/fulfillment/setup/delivery-expectations/automated-delivery-dates

5. MARKET_RATE_HIGHEST_ONLY_GATE
   Shopify blog 2026-10-01: when an order has more than one rate in a shipping option, only the highest matching rate applies. Do not sum.
   Source: https://www.shopify.com/blog/fulfillment-on-shopify-2026
   Store rates were not read.

Community viewed-vs-swiped bands were not encoded as pass/fail. They are not official thresholds.

PayoutLens was not modified. No store login, inventory write, or publish.
