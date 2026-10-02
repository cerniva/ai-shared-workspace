# Shopify bundle channel compatibility guard — 2026-10-02

- learning_id: `shopify-bundle-channel-compatibility-guard-2026-10-02`
- source_id: `shopify-help-product-bundles-official`
- affected_plan: `Video ve Shopify Otomasyonu / Shopify`
- status: `active`
- confidence: `high`
- discovered_at: `2026-10-02T20:19:33+03:00`
- last_verified: `2026-10-02T20:19:33+03:00`
- access_status: `web_verified_official`
- provenance: `https://help.shopify.com/en/manual/products/bundles`

## Finding
Shopify's official product-bundles documentation says bundles can be sold through Online Store, Shop, and Shopify POS, while the Google & YouTube sales channel supports fixed product bundles only. Therefore bundle eligibility is channel-specific; a bundle format that is valid on one channel must not be assumed valid on every sales channel.

## Previous approach
Bundle evaluation focused on demand, margin, inventory constraints, returns, and bundle-price drift, without an explicit sales-channel compatibility gate.

## Learned rule
Before recommending or publishing a bundle, identify the intended sales channel and verify that the bundle type is supported there. For Google & YouTube, treat only fixed bundles as supported unless newer official Shopify documentation supersedes this record. Channel compatibility is a pre-publish gate, not a demand or profitability signal.

## Test / metric
For each bundle candidate record `target_sales_channel`, `bundle_type`, and `channel_supported=true/false` from current official documentation. Do not publish or activate when `channel_supported=false/unknown`; route to a supported channel or choose a supported bundle type instead.

## Failure / fallback
If current official channel-compatibility documentation cannot be verified, mark the candidate `channel_support_unverified` and keep it draft-only. Do not infer support from virality, app UI, or search snippets.
