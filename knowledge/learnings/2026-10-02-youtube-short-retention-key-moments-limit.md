# YouTube Shorts retention key-moments limitation — 2026-10-02

- learning_id: `youtube-short-retention-key-moments-limit-2026-10-02`
- source_id: `youtube-help-audience-retention-official`
- affected_plan: `Video ve Shopify Otomasyonu / Shorts`
- status: `active`
- confidence: `high`
- discovered_at: `2026-10-02T23:20:28+03:00`
- last_verified: `2026-10-02T23:20:28+03:00`
- access_status: `web_only`
- provenance: `https://support.google.com/youtube/answer/9314415`
- finding: YouTube says audience-retention data typically takes 1–2 days to process. Its automatically highlighted key moments (intro/top moments/spikes/dips) require a video to be at least 60 seconds long and have at least 100 views. Therefore a 25–30 second Short should not be expected to receive those highlighted key-moment labels even when video-level retention data exists.
- old_approach: Treat key-moment labels as a generally available retention diagnostic for Shorts.
- new_rule: For 25–30 second Shorts, do not wait for or require YouTube's highlighted intro/top-moment/spike/dip labels. Evaluate available video-level retention plus stayed/chose-to-view, engaged views, AVD, APV and watch time after processing; use key-moment labels only when the video's eligibility conditions are actually met.
- test_metric: `retention_available`, `retention_processing_age_hours`, `stayed_to_watch`, `engaged_views`, `AVD`, `APV`, `watch_time`; key-moment labels are optional/not-applicable for sub-60-second Shorts.
- failure_history: `none`
- fallback_history: If highlighted key moments are absent on a sub-60-second Short, classify as `not_applicable_by_duration` rather than analytics failure; use the available retention curve/metrics instead.
