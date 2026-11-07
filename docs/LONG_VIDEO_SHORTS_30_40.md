# Long video → 30–40 second Shorts (proposal)

Scope: transform **owned or explicitly licensed** long videos into 30–40 second 9:16 clips. No generated replacement scenes. Do not upload or publish automatically.

## Pipeline
1. Intake: local video or authorized source URL, record provenance/license, reject missing rights.
2. Transcribe with timestamps (local Whisper when available); otherwise use a transcript provider with permission. Keep speech language.
3. Find 3–5 self-contained 30–40 second candidate segments; avoid cutting sentences; score hook, clarity, emotional payoff and context. Never assert viral success from a heuristic.
4. Render each candidate using FFmpeg (1080x1920, H.264/AAC). Prefer face/speaker tracking if available; fallback to center crop or blurred padding when subject would be cut off.
5. Burn readable, time-aligned subtitles; retain original audio, normalize loudness without clipping.
6. Run existing scripts/shorts_preflight.py against **the actual MP4**; require independent reviewer evidence tied to SHA256. Never set review flags automatically.
7. Save private MP4, transcript, source attribution, clip timecodes, scoring rationale and QC report as artifacts. Do not commit media or secrets.
8. Only after rights review and channel verification consider authorized upload. Reused-content monetization is not guaranteed.

## Tool selection and fallbacks
- Primary: local FFmpeg + Whisper + scoring logic, no paid credits.
- Optional discovery/selection: Chopify or ClipMint after checking license, security, dependencies and reproducible install.
- Optional hosted fallback: OpusClip/Vizard/CapCut with prior approval if credits, watermark, upload or fees are involved.
- If transcription fails: timestamped subtitles supplied by owner or manual review. If subject tracking fails: safe padded 9:16 frame.
- If no legal source: stop with RIGHTS_BLOCKED, do not download or republish.

## Acceptance tests (not yet run)
- 30 <= output duration <= 40 seconds; exact 9:16; H.264 + AAC.
- 100% video/audio decodes; no frozen or missing tail; audible voice, synced readable subtitles.
- Candidate begins and ends at natural sentence boundaries.
- Independent review checks copyright/rights, source context, correct channel, duplicate, audio/video and hook.
- Fail closed on missing source permission, empty transcript, invalid crop, missing independent review.
- Smoke test on a licensed >2 minute input, with artifact paths, hashes and logs.
