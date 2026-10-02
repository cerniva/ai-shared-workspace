# Shopify bundle constraint + margin guard — 2026-10-02

- learning_id: `shopify-bundle-constraint-margin-guard-2026-10-02`
- source_id: `shopify-help-bundles-official`
- affected_plan: `Video ve Shopify Otomasyonu / Shopify`
- status: `active`
- confidence: `high`
- finding: Shopify Bundles is a free first-party option for fixed bundles/multipacks. Bundle sellable quantity is constrained by the component with the lowest inventory coverage after accounting for required quantity. Component price changes do not automatically update the bundle price, so a bundle can silently lose contribution margin if component costs/prices change and the bundle price is not revalidated.
- old_approach: Evaluate bundle opportunity mainly as merchandising/AOV or slow-stock tactic after product-level demand and margin checks.
- new_rule: Before recommending/scaling a bundle, calculate component-constrained sellable quantity and revalidate bundle contribution margin against current component prices/costs, shipping, discount allocation, and return risk. Do not treat bundle demand as sufficient if a bottleneck component or stale bundle price makes fulfillment/margin unsafe.
- test_metric: `bundle_orders`, `bundle_total_sales`, component-constrained available bundle units, return-risk-adjusted contribution margin per bundle, stockout/cancellation rate.
- discovered_at: `2026-10-02T19:17:44+03:00`
- last_verified: `2026-10-02T19:17:44+03:00`
- access_status: `web_verified_official`
- failure_fallback: If store-level bundle analytics are unavailable, keep this as a pre-publish/reorder guard using verified component inventory and current economics; do not infer sales success from virality.
- provenance: Shopify Help Center official pages: Product bundles; Eligibility and considerations for using product bundles; Shopify Bundles.

## Decision impact

For candidate Shopify products that naturally combine or can be multipacked, bundles are a free-first test candidate only after the existing demand, landed-cost, shipping, quality/return, trust, policy, seasonality and differentiation gates pass. Publishing/pricing remains approval-gated. This rule adds a bundle-specific inventory bottleneck and stale-price/margin guard; it does not replace existing product economics rules.
