# YouTube Analytics dual-scope authorization gate

- learning_id: learn_youtube_analytics_dual_scope_gate_20261003
- source_id: src_google_youtube_analytics_reports_query_20261003
- topic: YouTube Analytics authorization / reusable integration reliability
- canonical_url: https://developers.google.com/youtube/analytics/reference/reports/query
- source_type: official_primary_documentation
- finding: The current official reports.query reference states that requests to this method now require access to the youtube.readonly OAuth scope. The broader Analytics reference also documents yt-analytics.readonly for viewing YouTube Analytics reports. Treat a working owned-channel Analytics query as requiring the scopes actually demanded by the current endpoint; do not assume yt-analytics.readonly alone is sufficient.
- evidence_confidence_limit: High for the documented scope requirement; no owned-channel OAuth request was executed in this cycle, so connection/runtime authorization remains unverified.
- affected_plans: Video/Shopify; Sistem Geliştirmeleri
- old_approach: Treat yt-analytics.readonly as the sole read scope needed for Analytics reporting.
- learned_rule: YOUTUBE_ANALYTICS_DUAL_SCOPE_GATE — before classifying owned-channel Analytics as verified_connected, require a successful reports.query response under the current documented authorization requirements. If an existing token lacks youtube.readonly, classify the Analytics path blocked/auth_scope until reauthorization succeeds; do not blind-retry 401/403.
- applied_test_next_measurement: On the next authorized owned-channel Analytics attempt, record request/API response evidence and distinguish missing-scope authorization failures from invalid_grant/token failures. Never expose token values.
- discovered_at: 2026-10-03T09:28:59+03:00
- last_verified: 2026-10-03
- access_status: web_only
- failure_history: No owned-channel reports.query call was available in this cycle; runtime scope status is therefore unknown.
- fallback: Preserve existing public/previously verified metrics and mark private Analytics fields unknown. Use current official docs for integration diagnosis; do not infer private channel data and do not retry auth failures blindly.
- provenance: Google for Developers — YouTube Analytics Reports: Query; cross-checked against YouTube Analytics API Reference.
- first_added_cycle: 2026-10-03-cycle-11
- last_used_cycle: 2026-10-03-cycle-11
- use_count: 1
- status: active

## Decision impact
This is an integration/authentication rule, not a performance heuristic. It prevents the system from misclassifying a scope-deficient OAuth token as a data/endpoint failure and provides a safer root-cause branch for the Video/Shopify and Sistem Geliştirmeleri plans.
