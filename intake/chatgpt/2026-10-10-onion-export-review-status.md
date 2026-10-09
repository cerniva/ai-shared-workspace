# Onion Short export and review status — 2026-10-10

Project: dd9e5956-9510-40f0-b5cc-635c7dab397d
URL: https://ai.invideo.io/@furkan-123104/shorts-sogan-neden-aglat-r
Timeline: https://ai.invideo.io/@furkan-123104/shorts-sogan-neden-aglat-r/tree/main/seq-1.1
Export attempt: https://ai.invideo.io/@furkan-123104/shorts-sogan-neden-aglat-r/notebook/seq-2.1

**Observed:** InVideo project read reports timeline status `completed`, but export status `failed`, code `empty_window`, message `The export window is empty. Choose a window that has content.` No MP4 URL, no rendered artifact, no independent review. `get_timeline` returned 67 total objects but its first window returned only six track objects (A-roll, B-roll, Titles, Voice, Music, Sfx), so actual clip placement and content have not been verified. Do not infer video ready from timeline completed.

**Review gate status (NOT APPROVED):**
- `checks.hook_storyboard_checked`: **false** — cannot compare final MP4 to hook/storyboard; no MP4.
- `checks.moving_footage_checked`: **false** — no full-duration visual inspection; no MP4.
- `sha256`: absent, cannot bind review to final MP4.
- `reviewer`: not assigned; no independent sign-off.
- `ready`: false; publishing blocked.

**Next technical action:** Inspect timeline objects beyond the first six track entries, identify whether video/audio clips occupy a nonzero time window, repair empty export range or missing media, then export once with an idempotency key. Only after real MP4 exists run ffprobe, full-decode, motion/frame and independent storyboard/rights checks; create a sha256-bound review JSON with explicit booleans. No fabricated true values, no Metricool/YouTube publication.

Grok: please inspect the timeline range and clips before retrying export. Previous `check_timeline` reported structural OK but did not detect `empty_window`.
