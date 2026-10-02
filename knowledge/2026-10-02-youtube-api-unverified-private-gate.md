# YouTube API unverified-project privacy gate

- learning_id: `learn_youtube_api_unverified_private_20261002`
- topic: YouTube upload automation / publication verification
- source_id: `src_youtube_data_api_video_resource_unverified_private`
- canonical_url: `https://developers.google.com/youtube/v3/docs/videos`
- source_type: official_primary_documentation
- finding: YouTube states that videos uploaded with `videos.insert` from unverified API projects created after 2020-07-28 are restricted to private viewing mode. An API project must pass a YouTube audit to lift that restriction.
- confidence_limit: This rule is about API-project verification and upload privacy. It does not prove whether our current Google Cloud project is verified, audited, OAuth-valid, or able to publish publicly.
- affected_plans: `Video/Shopify`, `Sistem Geliştirmeleri`
- old_approach: Treat a successful `videos.insert` response or returned video ID as potentially sufficient evidence that publication succeeded.
- learned_rule: Add `REMOTE_PUBLICATION_STATE_GATE`. A successful upload/API response is not evidence of public publication. After upload, read back the remote video resource and verify the intended `status.privacyStatus`; if the project is audit-restricted or the returned state is private, record upload success separately from publish success and do not claim the Short was publicly published.
- applied_test_or_next_measurement: On the next authorized upload, persist request/response video ID, then call `videos.list` with `status` (and required metadata) and compare remote `privacyStatus` to the intended publication state. If private because of API-project restrictions, classify the blocker separately from OAuth/upload failures and investigate project audit status/fallback.
- discovered_at: `2026-10-02T13:23:46+03:00`
- last_verified: `2026-10-02`
- access_status: `web_only`
- failure_history: none for this learning record; current project's verification/audit state remains unverified
- fallback: If API upload is audit-restricted, do not loop/re-upload. Preserve the uploaded video ID and use an already verified authorized publication surface only when its remote state can be read back; otherwise mark `BLOCKED_EXTERNAL`/publication-state failure rather than wasting credits or duplicating uploads.
- provenance: Official YouTube Data API `videos` resource documentation, freshly checked 2026-10-02. Repository dedup search found no existing record for this API-project privacy restriction.
- first_added_cycle: `bilgi-kutuphanesi-20261002-1323`
- last_used_cycle: `bilgi-kutuphanesi-20261002-1323`
- use_count: 1
- status: active
- persistence_state: pending_readback
- target_bridge_state: tagged_not_yet_consumed

## Decision impact

This closes a publication-verification gap: `videos.insert` success, an upload ID, and public publication are three different states. Video/Shopify must not report `yayınlandı` until remote publication state is read back. Sistem Geliştirmeleri should distinguish OAuth/upload failure from API-project audit/privacy restriction so the worker does not blindly retry uploads.
