# SHORTS_COHORT_TRAFFIC_SOURCE_GATE

- checked: 2026-10-04
- source: https://developers.google.com/youtube/analytics/dimensions
- machine_status: script gate only; not a new learning_ledger row
- pool_kept: story_phase, normalized retention, A/V event, cohort evidence, Shopify variant/inventory/ETA/shipping/publication checks
- payoutlens: untouched

insightTrafficSourceType is how the viewer arrived. creatorContentType SHORTS is what was watched. They are not interchangeable.

SHORTS traffic source means a vertical swipe in the Shorts viewing experience. Official detail list does not define insightTrafficSourceDetail for SHORTS. Do not infer it.

HASHTAGS, SOUND_PAGE and VIDEO_REMIXES are separate sources. VIDEO_REMIXES detail, when present, is the referring remixed video, not a swipe proof.

YT_SEARCH detail is the search term. EXT_URL detail is the web page and includes Google Search referrals.

Missing authorized source stays unknown. Raw views are not a source mix. Correlation is not causality. No owned-channel query was run.
