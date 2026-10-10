# Shorts success patterns (Cerno)

Last updated: 2026-10-10. Every render packet with `free_render_requested: true` must reference this file in
`learnings.success_patterns` and list how it was applied (`learnings.applied`); `scripts/shorts_research.py`
gate blocks it otherwise.

Labels: **[SOURCED]** = stated by an official YouTube source (URL given). **[OBSERVED]** = our own channel data
(Cerno, TinyFish Studio read run 37991566901, 2026-09-11..2026-10-08: 5,300 views, 9.5 watch h, +6 subs;
top: Mbappé 2,610, airplane window 1,219, airplane seat 1,122). Observations are small-sample, not causal proof.
**[RULE]** = our operating decision derived from the above.

## 1. Hook (first 1–3 s)
- [SOURCED] "You have one second to hook someone, especially on Shorts"; formula shock → intrigue → satisfy.
  YouTube Blog / Creator Insider conversation (Todd Sherman, Jenny Hoyos):
  https://blog.youtube/creator-and-artist-stories/youtube-shorts-deep-dive/
- [SOURCED] "Capture attention in the first few seconds to prevent viewers from scrolling."
  https://blog.youtube/creator-and-artist-stories/your-guide-to-getting-started-with-youtube-shorts/
- [SOURCED] Studio measures this as "Stayed to watch" (viewed vs swiped away): the percentage of times viewers
  stayed past the initial seconds. https://support.google.com/youtube/answer/12220281
- [OBSERVED] Our best Short (Mbappé, 49% of 28-day views) opened on a direct question about a known person.
- [RULE] Frame 1 = motion + on-screen question; no greeting/intro ("merhaba", "bugün size", "bu videoda" are
  already blocked by the gate). Judge hooks by stayed-to-watch, not raw views.

## 2. Length
- [SOURCED] Shorts can be up to 3 minutes (square/vertical, uploaded on/after 2024-10-15).
  https://blog.youtube/news-and-events/tall-updates-coming-to-shorts/ ·
  https://support.google.com/youtube/answer/15424877
- [SOURCED] Creators also succeed with very short ~15 s "moments"; storytelling should be concise "bits".
  https://blog.youtube/creator-and-artist-stories/youtube-shorts-deep-dive/
- [OBSERVED] ~6.5 s watched per view on average (9.5 h / 5,300 views) — long Shorts would mostly be unwatched.
- [RULE] Concept tests ≤ 30 s (enforced by learn_53ca8fb858703eb6 in `shorts_learnings.py`); extend only after a
  video shows average % viewed ≥ 70.

## 3. Pacing
- [SOURCED] Average view duration / average percentage viewed for Shorts are computed from engaged views
  (viewers who stayed). https://support.google.com/youtube/answer/9314355
- [OBSERVED] Low watch-per-view → viewers leave early; no evidence yet on mid-video drop points.
- [RULE] New visual every 2–4 s, one idea per beat (3 beats max for 30 s), payoff before second 25, loop ending
  that matches frame 1.

## 4. Topic choice
- [SOURCED] Trends help new creators start, but original ideas "last a lot longer"; early likes-to-views ratio is
  used as a quick signal. https://blog.youtube/creator-and-artist-stories/five-tips-to-master-shorts/
- [SOURCED] Trends tab in Analytics surfaces what your audience searches for (content gaps).
  https://support.google.com/youtube/answer/9002587
- [OBSERVED] Top 3 Shorts = 93% of views: famous-athlete mechanics and everyday-aviation curiosities.
- [RULE] Prefer repeatable series in these two families (sports mechanics, airplane "why" facts); one variable
  changed per test; no broadcast clips or unlicensed faces.

## 5. Title / thumbnail
- [SOURCED] Thumbnails matter less for initial Shorts discovery (feed), but help channel branding.
  https://blog.youtube/creator-and-artist-stories/youtube-shorts-deep-dive/
- [OBSERVED] Not enough data on titles yet.
- [RULE] Title = the hook question or its answer-promise, ≤ 60 chars, names the subject (e.g. person/object);
  thumbnail frame = the clearest motion frame with the question text.

## 6. Measurement
- [SOURCED] Since 2025-03-31 Shorts "views" count every start/replay; "engaged views" keep the old stricter count.
  https://support.google.com/youtube/answer/12220281
- [SOURCED] Analytics API exposes views, engagedViews, averageViewDuration, averageViewPercentage, likes,
  subscribersGained; it does not expose Shorts "stayed to watch".
  https://developers.google.com/youtube/analytics/metrics
- [RULE] 48h after each upload `shorts-48h-lessons.yml` appends a lesson to `video-lessons.md`; weekly notes in
  `weekly-YYYY-WW.md` aggregate. Read stayed-to-watch via the TinyFish Studio read.

Creator Insider channel (official YouTube team channel): https://www.youtube.com/@CreatorInsider
