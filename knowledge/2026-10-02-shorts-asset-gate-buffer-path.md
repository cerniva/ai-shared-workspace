# Shorts asset gate and Buffer publish path — 2026-10-02

- learning_id: learn_shorts_asset_gate_buffer_path_20261002
- topic: YouTube Shorts production / authorized publish fallback
- source_id: src_owned_cerno_public_shorts_20261002
- finding: The repo file shorts/shorts_bugun.mp4 is 18.0s, 1080x1920, H.264 24fps, AAC stereo, mean_volume -30.1 dB, max_volume -10.4 dB, blob sha 14f34ef7110b6052a79d434bd80d7d087e6a4f0b. Sampled frames at 0s, ~5s and ~15s are text cards on a dark field, not rights-safe real moving footage. It fails the 25–30s and no-slideshow gates, so it must not be published as today's Short.
- confidence: High for local ffprobe/frame read-back of the repo blob. Public view counts below are YouTube public metadata only, not Studio engaged views, AVD, APV or retention curves.
- affected_plans: Video/Shopify
- old_approach: Treat today's rendered MP4 plus a provider success as a publish candidate, and treat Metricool as the only live publish path.
- learned_rule: ASSET_DURATION_MOTION_GATE — do not send a Short to any publisher unless the exact MP4 is 25–30s, 9:16, has real motion across the full duration, has audible AAC, and passes semantic A/V QA. PUBLISH_PATH_SPLIT — Metricool blog 2621658 403 and direct YouTube OAuth invalid_grant stay unretriable. Buffer organization 6ab82d136c0a6dd3454cb756 channel 6ab82e66ea19ca0bdef9e5ec (Cerno, service youtube, isDisconnected=false) is an authorized candidate path only. A Buffer post is not DONE until a remote YouTube video ID/URL/status is read back.
- applied_test_or_next_measurement: Next production must be a new visual set. After an authorized publish, read back the YouTube ID and privacy/public status. Do not count Buffer or Metricool HTTP success alone.
- discovered_at: 2026-10-02T18:07:00+03:00
- last_verified: 2026-10-02T18:07:00+03:00
- access_status: buffer_channel_connected_not_used; metricool_403_not_retried; youtube_oauth_invalid_grant_not_retried; studio_analytics_not_accessed
- failure_history: Metricool publish read-back 403 Access denied to blog 2621658 reported by ChatGPT 2026-10-02; not retried. Direct OAuth remains invalid_grant in state/now.json; not retried.
- fallback: Buffer YouTube channel above, unused this cycle because the asset failed the gate. No untested provider marked working.
- provenance: Repo blob ffprobe; frame sample; Buffer list_channels 2026-10-02T18:06+03; public https://www.youtube.com/@cernodaily/shorts retrieved 2026-10-01.
- status: active
- persistence_state: pending_readback
