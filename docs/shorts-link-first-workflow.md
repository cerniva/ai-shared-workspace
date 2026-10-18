# Link-first Shorts curation (no TTS or MP4 rendering)

Goal: find existing compelling videos and deliver 30–40-second timestamped clip recommendations for manual editing. No narration generation, FFmpeg render, media download, upload, or paid credits.

## Output for each candidate
- Original URL, creator, title and publication date
- Verified license or explicit commercial reuse permission, with evidence URL and checked date; status `verified` or `blocked`
- Start/end timestamps (30–40 seconds) based on viewing the actual video, with hook and ending rationale
- Existing audio status and music/third-party rights separately checked
- Suggested editor or YouTube-native Remix link, and any limitations
- Source metrics (views/engagement) only if observed, with timestamp and source
- Monetization risk: YouTube reused-content policy requires meaningful original contribution, not just clipping

## Workflow
1. Discover promising videos by topic and public popularity indicators; do not treat virality as permission.
2. Filter for source-specific CC BY, public domain, or written commercial adaptation permission. Preserve evidence and attribution requirements. YouTube Remix eligibility only authorizes the in-platform feature's permitted scope, not unrestricted downloads.
3. Watch candidate and record accurate in/out points and hook. If video cannot be watched, mark timestamps `unverified`, never invent.
4. Deliver five candidates with links, verified rights and editor steps. No new voiceover required; preserve original sound only when audio rights permit.
5. Human publishes only after licensing and monetization/reused-content review; no automated publishing.

Sources: https://support.google.com/youtube/answer/2797468 ; https://support.google.com/youtube/answer/2490020 ; https://www.pexels.com/license/ ; https://creativecommons.org/reusing-cc-licensed-content/

Existing shorts-free-build and shorts-free-smoke-once workflows are legacy render tests, not prerequisites for this link-first process. Do not conflate green CI with a published Short. PayoutLens excluded.
