# YouTube view-count timeline correction

Status: active
Learning ID: learn_youtube_view_timeline_20261002
Affected plans: Video/Shopify, Bilgi Kütüphanesi
Checked: 2026-10-02

## Official sources
- Google Developers — YouTube Analytics/Reporting revision history: https://developers.google.com/youtube/reporting/revision_history
- Google Developers — YouTube Analytics metrics: https://developers.google.com/youtube/analytics/metrics
- YouTube Help — Understand your YouTube content performance: https://support.google.com/youtube/answer/12220281

## Finding
There are two distinct metric discontinuities that must not be collapsed into one date.

1. Shorts-specific change: starting 31 March 2025, YouTube changed Shorts `views` so a view counts when a Short starts to play or replay, with no minimum watch-time requirement. The Targeted Queries API followed on 30 April 2025; `engagedViews` preserves the prior Shorts view-counting methodology for authorized analytics.
2. All-format change: beginning 24 August 2026, YouTube Help states that views are counted when a video starts to play across Shorts, VOD and live. YPP earnings/eligibility continue to use engaged/qualified measures rather than the new raw-start view count.

## Decision / learned rule
For Shorts historical analysis, do not use 24 August 2026 as the only comparability break. Treat 31 March 2025 (and the API rollout on 30 April 2025 when querying Analytics/Reporting) as the Shorts-specific raw-view methodology break. Treat 24 August 2026 as the broader all-format counting change. For production learning, prefer owned `engagedViews`, average view duration/percentage, stayed-to-watch/retention and watch time when available; label any cross-regime raw-view comparison with the relevant methodology break.

## Supersedes / corrects
This refines `knowledge/2026-10-02-youtube-shorts-metric-change.md`, which correctly records the 24-Aug-2026 all-format change but is insufficient as the sole Shorts historical breakpoint.

## Confidence and limits
Confidence: high; official YouTube/Google documentation. Metric availability still depends on authorized channel analytics and report type. This rule does not imply causation between any metric and recommendation performance.

## Next measurement
When owned channel analytics are available, query the same Shorts using `engagedViews`, average view duration/percentage and retention/stayed-to-watch where supported; avoid interpreting raw-view deltas across the 2025/2026 methodology boundaries as content-quality changes without normalization or a methodology note.
