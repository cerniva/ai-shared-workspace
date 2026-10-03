# RETENTION_REWATCH_BASELINE_GATE

- learning_id: `learn_youtube_retention_rewatch_baseline_gate_20261003`
- source_id: `youtube-analytics-metrics-official`
- topic: YouTube audience retention interpretation
- canonical_url: https://developers.google.com/youtube/analytics/metrics
- source_type: official primary documentation
- finding: `audienceWatchRatio` is an absolute per-segment watch ratio and can exceed 1.0 when viewers rewatch a segment. `relativeRetentionPerformance` is a separate 0..1 comparison against YouTube videos of similar length; 0.5 is the median relative position, not 50% of viewers retained.
- evidence_confidence_limit: Official API semantics verified 2026-10-03. This does not prove why a particular Short performed or provide owned-channel values.
- affected_plans: Video/Shopify; Sistem Geliştirmeleri
- old_approach: Treat a retention value above 100% as invalid/analytics failure, or read relativeRetentionPerformance=0.5 as 50% viewer retention.
- learned_rule: `RETENTION_REWATCH_BASELINE_GATE` — preserve the metric name and denominator. audienceWatchRatio > 1 is valid evidence of repeated segment viewing, not automatically bad data. relativeRetentionPerformance is a similar-length benchmark rank-like score and must not be relabeled as absolute viewer retention. Do not infer causality from either metric alone.
- applied_test_next_measurement: On the next authorized mature single-video retention report, query elapsedVideoTimeRatio with audienceWatchRatio and relativeRetentionPerformance; preserve values >1 and compare the two series without converting one into the other.
- discovered_at: 2026-10-03T18:23:25+03:00
- last_verified: 2026-10-03T18:23:25+03:00
- access_status: web_only
- failure_history: Machine-ledger write is not yet proven in this run; standalone record must not be called full persistence until learning_ledger.json contains this learning_id and target-plan consumption is evidenced.
- fallback: If authorized retention data is unavailable, keep segment-level rewatch/relative baseline unknown and use mature engagedViews, AVD/APV and watch time without inventing retention values.
- provenance: Google Developers — YouTube Analytics Metrics; Google Developers — Channel Reports
- first_added_cycle: 2026-10-03-cycle-11
- last_used_cycle: 2026-10-03-cycle-11
- use_count: 1
- status: active_candidate
- persistence_status: PERSISTENCE_FAILURE_machine_ledger_unverified
- bridge_status: bridge_failure_target_plan_consumption_unverified

PayoutLens is out of scope and was not modified.
