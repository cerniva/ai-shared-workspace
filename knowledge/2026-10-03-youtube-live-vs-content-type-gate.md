# YouTube LIVE_ACTIVITY_CONTEXT_GATE

- learning_id: learn_youtube_live_activity_context_gate_20261003
- source_id: src_youtube_analytics_dimensions_live_or_on_demand
- topic: youtube analytics / live activity context
- canonical_url: https://developers.google.com/youtube/analytics/dimensions
- source_type: official_primary_documentation
- finding: `creatorContentType` and `liveOrOnDemand` answer different questions. `creatorContentType=LIVE_STREAM` classifies the viewed content as a livestream, while `liveOrOnDemand=LIVE` means the measured user activity occurred during a live broadcast and `ON_DEMAND` means it did not occur during a live broadcast. Do not substitute one dimension for the other.
- evidence_confidence_limit: High confidence for API semantics from official YouTube Analytics dimensions documentation. No owned-channel authenticated response was executed in this cycle, so runtime availability/coverage for this channel remains unverified. Creator/YouTube discovery material was not promoted above the primary documentation.
- affected_plans: Video/Shopify; Sistem Geliştirmeleri
- old_approach: Content type alone could be treated as sufficient to describe live-vs-on-demand viewing context.
- learned_rule: LIVE_ACTIVITY_CONTEXT_GATE — use `creatorContentType` for content-format classification and `liveOrOnDemand` for whether activity occurred during the live broadcast. Never infer live-session activity solely from `creatorContentType`, and never infer the content taxonomy solely from `liveOrOnDemand`.
- applied_test_next_measurement: On an authenticated mature report, test supported `creatorContentType` + `liveOrOnDemand` segmentation with engagedViews/watch time where the channel report schema allows it; compare only descriptive segments, not causal effects.
- discovered_at: 2026-10-03T14:30:00+03:00
- last_verified: 2026-10-03
- access_status: web_only
- failure_history: No owned-channel Analytics API response in this cycle; target-plan runtime consumption unverified.
- fallback: If `liveOrOnDemand` is unavailable, keep live-session context `unknown`; do not derive it from Shorts feed, playback location, or `creatorContentType` alone.
- provenance: Google for Developers YouTube Analytics Dimensions; YouTube official live-streaming/help discovery checked as secondary context.
- first_added_cycle: 2026-10-03T14:30+03:00
- last_used_cycle: 2026-10-03T14:30+03:00
- use_count: 1
- status: active
- persistence_status: write_read_back_pass
- bridge_status: bridge_failure_target_plan_consumption_unverified

PayoutLens untouched. No secrets/PII.