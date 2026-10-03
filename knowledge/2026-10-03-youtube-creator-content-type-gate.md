# YouTube creator content type gate

learning_id: learn_youtube_creator_content_type_gate_20261003
source_id: src_youtube_analytics_dimensions_creator_content_type
status: active
discovered_at: 2026-10-03T07:28:00+03:00
last_verified: 2026-10-03T07:28:00+03:00
access_status: web_only
plans: Video/Shopify, Sistem Geliştirmeleri
provenance: Google for Developers — YouTube Analytics dimensions
canonical_url: https://developers.google.com/youtube/analytics/dimensions

## Finding
YouTube Analytics exposes `creatorContentType`, available for dates from 2019-01-01, with values including `SHORTS`, `LIVE_STREAM`, `STORY`, `VIDEO_ON_DEMAND`, and `UNSPECIFIED`. This is a content-type dimension, distinct from `liveOrOnDemand`, traffic source, playback location, and subscribed status.

## CREATOR_CONTENT_TYPE_GATE
When authorized mature Analytics is available, use `creatorContentType=SHORTS` (or an equivalent supported report/filter) to keep Shorts measurements scoped to Shorts when comparing channel-level content-format performance. Do not infer Shorts membership from traffic source `SHORTS`: that traffic-source value means the viewer was referred by vertical swiping in the Shorts viewing experience, not that every measured content row is itself classified as Shorts. Do not combine unsupported metric/dimension/filter combinations; if the authorized query rejects the combination, preserve the error and keep the format context unknown rather than guessing.

## Evidence / confidence limit
Primary official documentation verified 2026-10-03. This establishes dimension semantics and availability, not owned-channel values, performance causality, or guaranteed compatibility with every metric combination.

## Previous approach
Shorts analysis already separated public views, engagedViews, retention, traffic source, playback location, device context, subscribed status, sharing service, and audience loyalty, but lacked an explicit gate separating content classification from referral source.

## New reusable rule
Content type answers *what was watched*; traffic source answers *how the viewer reached it*. Keep those dimensions semantically separate.

## Test / next measurement
On the next authorized mature channel Analytics read, query a documented report supporting `creatorContentType` and record whether `SHORTS` can be paired with the required quality metrics. If unsupported, record the API error and use a verified video-ID set as fallback without relabeling traffic-source `SHORTS` as content type.

failure_history:
- No authorized owned-channel Analytics query was executed in this cycle; plan-consumption PASS is not claimed.
- Central learning_ledger update is not claimed in this cycle because the connector returned the large JSON as a truncated single-line payload, making safe whole-file replacement impossible without risking existing records.

fallback:
- Keep this stable standalone knowledge record read-backable on main.
- Next cycle, dedup against this learning_id first. If a safe machine-ledger writer/path is available, bridge this record into the central ledger and read it back before marking bridge PASS.

first_added_cycle: 2026-10-03T07:28:00+03:00
last_used_cycle: 2026-10-03T07:28:00+03:00
use_count: 1

## Bridge read-back 2026-10-03T07:34:00+03:00

Markdown-only note remained fail-closed until this append. Machine row learn_f39d67f1d7f48c87 uses catalog source src_62a331e31269e5a6 (canonical https://developers.google.com/youtube/analytics/dimensions). The note's src_youtube_analytics_dimensions_creator_content_type is not a catalog id. Gate command persisted true, learning_count 29. Owned-channel query still not run. Plan-consumption PASS is not claimed.
