# YouTube device context analytics gate

- learning_id: `learn_youtube_device_context_20261003`
- topic: YouTube Shorts analytics / device context
- canonical_url: `https://developers.google.com/youtube/reporting/v1/reports/dimensions`
- source_type: official_primary_documentation
- finding: YouTube Reporting supports `device_type` and `operating_system` dimensions. Device type distinguishes computer, TV, game console, mobile phone, tablet and unknown. Device/OS context is analytically distinct from traffic source and playback location. Targeted Analytics reports also enforce supported dimension/metric/filter combinations, so unsupported cross-dimension joins must not be invented.
- confidence_limit: Official API capability is verified from Google documentation. No authorized channel query was executed in this cycle, so no claim is made about this channel's device distribution or performance.
- affected_plans: [Video/Shopify, Sistem Geliştirmeleri]
- old_approach: Evaluate Shorts mainly with views/engagedViews, retention, traffic source, playback location and conversion signals without explicitly separating viewing-device context.
- learned_rule: `DEVICE_CONTEXT_GATE` — when authorized data is available, segment engaged viewing/watch-time by supported device/OS reports before interpreting format performance. Treat device context as descriptive segmentation, not proof of algorithmic causality. Never fabricate an unsupported traffic-source × playback-location × device cross-join; use only combinations documented/successfully returned by the API.
- applied_test: Official Reporting dimensions and Analytics channel-report query constraints were checked. No live channel request was available in this cycle.
- next_measurement: For a mature Short, request a supported device-type/OS report with engagedViews/watch-time, then test whether editing/readability decisions differ materially by device mix.
- discovered_at: 2026-10-03T01:25:26+03:00
- last_verified: 2026-10-03
- access_status: web_only
- failure_history: [authorized_channel_device_query_not_executed]
- fallback: If authorized device data is unavailable, retain existing verified engagedViews/retention/traffic-source/playback-location layers and mark device context `unknown`; do not infer it from public views.
- provenance: Google for Developers — YouTube Reporting API Dimensions; YouTube Analytics Channel Reports.
- first_added_cycle: 2026-10-03T01:25:26+03:00
- last_used_cycle: 2026-10-03T01:25:26+03:00
- use_count: 1
- status: active

## Decision value

This closes a distinct context gap: *where the viewer came from* (traffic source), *where playback happened* (playback location), and *what device class was used* are separate analytical questions. The production loop should preserve those distinctions and only combine dimensions when the documented report schema or a successful API response supports the combination.


## Machine ledger persistence 2026-10-03T01:34+03:00

- machine_learning_id: `learn_f29ec85ba0bcaccd`
- source_ids: `src_8114d88826736507`, `src_d1eebde122d891b3`, `src_62a331e31269e5a6`
- note: knowledge_index.json does not store per-learning rows. machine_learnings.path is knowledge/learning_ledger.json. Persistence is the ledger row, not a second copy inside the index.
- Reporting nuance: channel_combined_a3 documents playback_location_type + traffic_source_type + device_type + operating_system as a Reporting API bulk schema. That does not authorize an undocumented Analytics API query.
