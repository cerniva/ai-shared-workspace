# YouTube Shorts view metric change — 2026-10-02

- learning_id: `video-youtube-shorts-view-metric-2026-08-24`
- source_id: `youtube-help-content-performance-12220281`
- affected_plan: `Video ve Shopify Otomasyonu / Shorts`
- status: `active`
- confidence: `high`
- access_status: `web_verified_official`
- discovered_at: `2026-10-02T18:19:43+03:00`
- last_verified: `2026-10-02T18:19:43+03:00`
- provenance: `Official YouTube Help — Understand your YouTube content performance (answer/12220281)`
- finding: `Beginning 2026-08-24, YouTube counts a view when a video starts to play across Shorts, VOD and live. YPP earnings remain based on engaged Shorts views / engaged watch hours, and Shorts analytics separately exposes engaged views, stayed-to-watch (viewed vs swiped away), AVD and APV.`
- old_approach: `Raw public/view-count changes could be treated as roughly comparable with older Shorts performance periods.`
- learned_rule: `Do not compare post-2026-08-24 raw Shorts views directly with pre-change raw views as the primary performance signal. For creative decisions prioritize stayed-to-watch/chose-to-view, engaged views, AVD, APV, watch time, retention and subscriber/engagement outcomes; annotate metric-definition era when using raw views.`
- test_metric: `For each new Short record publish date, raw views, engaged views, stayed-to-watch, AVD, APV, retention/watch time and subscriber/engagement signals; compare like-for-like post-change cohorts.`
- failure_fallback: `If owned analytics is unavailable, public raw views may be logged only as weak discovery evidence, not as proof of hook/retention quality.`
- supersedes: `Any implicit rule that treats raw Shorts views before and after 2026-08-24 as directly comparable without qualification.`
- persistence_requirement: `Must be discoverable in CURRENT_KNOWLEDGE_SET on the next automation turn; otherwise flag PERSISTENCE_FAILURE.`

PayoutLens is out of scope and untouched.
