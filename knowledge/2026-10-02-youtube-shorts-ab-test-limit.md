# YouTube Shorts native A/B-test limitation

Status: active
Learning ID: learn_youtube_shorts_ab_limit_20261002
Affected plans: Video/Shopify, Bilgi Kütüphanesi
Checked: 2026-10-02

## Official source
- YouTube Help — A/B test titles and thumbnails: https://support.google.com/youtube/answer/16391400

## Finding
YouTube Studio's native concurrent A/B test can test up to three titles/thumbnails for eligible long-form videos and chooses results using watch-time performance, but the official eligibility rules explicitly exclude Shorts. A video that transitions into a Short also cannot use the native A/B test.

## Decision / learned rule
For Shorts, do not claim that YouTube Studio native title/thumbnail A/B testing was run or that a native A/B winner exists. Treat hook/title/packaging changes as sequential production experiments unless a separate verified experiment mechanism is available. Compare Shorts primarily with owned engagedViews, stayed-to-watch/retention, average view duration/percentage, watch time and satisfaction/engagement signals where available, while controlling for topic, publish timing and view-count methodology changes. Native YouTube A/B-test conclusions may be used for eligible long-form content only, not transferred as direct Shorts experiment evidence.

## Confidence and limits
Confidence: high; official YouTube Help. This does not prohibit creative iteration on Shorts titles or first-frame packaging; it only prevents labeling that iteration as YouTube Studio's native concurrent A/B test.

## Dedup
Repository search before write found no existing knowledge entry for the Shorts native A/B-test exclusion.

## Next measurement
On the next owned-channel Shorts analytics read, record whether engagedViews, stayed-to-watch/retention and AVD/APV are available for comparable Shorts and use those metrics for sequential experiment evaluation.
