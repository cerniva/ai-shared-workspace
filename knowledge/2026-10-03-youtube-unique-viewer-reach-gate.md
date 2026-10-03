# YouTube unique viewer reach gate

- learning_id: `learn_youtube_unique_viewer_reach_gate_20261003`
- source_id: `youtube-help-audience-unique-viewers-2026`
- topic: YouTube Shorts analytics / unique audience reach
- canonical_url: https://support.google.com/youtube/answer/9314416
- source_type: official_primary_web
- finding: YouTube Studio defines Unique viewers as an estimated number of viewers in the selected date range, calculated from engaged views and corresponding watch time. It is not the same as public views, engagedViews, subscribers, or returning viewers. Because it is an estimate, public view counts must not be divided or otherwise transformed to invent a unique-viewer count.
- evidence_limit: Official Studio documentation defines the metric and estimation basis, but this run did not perform an authorized owned-channel Audience read-back. No owned-channel unique-viewer value is claimed.
- affected_plans: Video/Shopify; Sistem Geliştirmeleri
- old_approach: Reach analysis could over-rely on raw/public views and repeat-audience segments without a separate unique-audience denominator.
- learned_rule: `UNIQUE_VIEWER_REACH_GATE` — when authorized mature Studio Audience data exists, keep unique viewers as a separate estimated reach layer and use it for like-for-like audience-size comparisons. Never substitute public views or engagedViews for unique viewers, and never infer unique viewers from public metrics.
- test_or_next_measurement: On the next authorized mature owned-channel read, record the selected date window, unique viewers, engagedViews and watch time from the same comparable period; compare formats only on like-for-like windows and preserve the estimate label.
- discovered_at: 2026-10-03T03:22:19+03:00
- last_verified: 2026-10-03
- access_status: web_only
- failure_history: []
- fallback: If authorized Studio Audience unique-viewer data is unavailable, keep unique viewers `unknown`; continue with verified engagedViews, retention and audience-loyalty signals without estimating unique audience.
- provenance: Official YouTube Help documentation; creator/search discovery was not used as proof.
- first_added_cycle: 2026-10-03T03:22:19+03:00
- last_used_cycle: 2026-10-03T03:22:19+03:00
- use_count: 1
- status: active

## Decision value

This closes a measurement gap between playback counts and audience size. A Short can accumulate multiple views/engaged views from the same people; unique viewers is therefore a distinct estimated reach layer. The gate prevents raw views from being misreported as audience size and gives Video/Shopify a safer denominator for comparing audience breadth across mature, like-for-like periods.

## YouTube / internet research handling

Internet research checked current official YouTube Audience documentation. YouTube/creator discovery was treated only as discovery; no creator claim was persisted because the official primary definition was sufficient.
