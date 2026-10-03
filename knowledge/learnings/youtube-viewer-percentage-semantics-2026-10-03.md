# YouTube viewerPercentage semantics gate

- learning_id: learn_youtube_viewer_percentage_semantics_20261003
- topic: youtube-shorts-analytics
- source_id: src_youtube_analytics_metrics_viewer_percentage
- canonical_url: https://developers.google.com/youtube/analytics/metrics
- source_type: official_primary_documentation
- finding: YouTube Analytics defines viewerPercentage as the percentage of viewers who were logged in while watching the video or playlist. It is not averageViewPercentage and must not be interpreted as the percentage of a video watched. averageViewPercentage is a separate watch-time metric.
- evidence_confidence_limit: Official primary API documentation verifies the metric semantics, but no owned-channel authenticated viewerPercentage response was available in this run. No claim is made about this channel's logged-in viewer share or retention.
- affected_plans: [Video/Shopify, Sistem Geliştirmeleri]
- old_approach: A percentage-labeled Analytics field could be misread or normalized as a viewing-completion/retention percentage without checking its metric definition.
- learned_rule: VIEWER_PERCENTAGE_SEMANTICS_GATE — keep viewerPercentage and averageViewPercentage as separate typed metrics. viewerPercentage = share of viewers logged in; averageViewPercentage = average percentage of the video watched. Never use viewerPercentage as retention, completion, satisfaction, or subscriber share. If the field is unavailable, mark logged-in-viewer share unknown.
- applied_test_next_measurement: On the next authorized mature owned-video Analytics read, retrieve viewerPercentage only in a documented supported report and keep it separate from engagedViews, averageViewDuration, averageViewPercentage and retention. Record whether this context changes any audience-interpretation decision; do not infer missing values.
- discovered_at: 2026-10-03T20:29:00+03:00
- last_verified: 2026-10-03T20:29:00+03:00
- access_status: web_only
- failure_history: [Machine-ledger insertion and target-plan runtime consumption are not yet verified in this run; standalone Markdown must not be treated as full persistence.]
- fallback: If authorized viewerPercentage is unavailable, leave logged-in-viewer share unknown and continue with mature engagedViews, AVD/APV, retention and watch-time evidence without substitution.
- provenance: verified_official_primary
- first_added_cycle: 2026-10-03T20:29:00+03:00
- last_used_cycle: 2026-10-03T20:29:00+03:00
- use_count: 1
- status: active
- persistence_status: pending_read_back
- bridge_status: bridge_failure_target_plan_consumption_unverified

## YouTube research layer

Official YouTube for Artists education recommends using multiple audience/performance measures such as views, watch time, unique viewers, subscribers, and new/returning users rather than collapsing audience interpretation into one percentage. This supports the typed-metric approach but is not used as the primary evidence for viewerPercentage semantics.
