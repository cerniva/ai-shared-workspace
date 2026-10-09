# HO-20261010-12 — free alternative and independent QC status

Status: BLOCKED_MP4 (not approved for upload). Date: 2026-10-10.

## Observed evidence
- InVideo project dd9e5956-9510-40f0-b5cc-635c7dab397d: prior export failed with code `empty_window`; no downloadable MP4 URL verified.
- Timeline clip and audio_clip collections were read and both returned zero objects; a project timeline marked completed does not prove rendered media.
- Manus report at `messages/apps/manus.md`, APP-MANUS-20261010-01-R1: private project inaccessible from its browser; no MP4 produced.
- `scripts/shorts_free_pipeline.py` exists on main and prepares render.json, local visual assets, narration and subtitles, then invokes local renderer. This is a **candidate** free path, not proof that a compliant MP4 was built.
- `knowledge/lessons.md` HO-11 lesson `qc-flag-is-not-check`: review flags alone are not evidence of actual inspection.
- An attempted GitHub workflow artifact lookup for run 38000057827 returned no artifacts. Reported artifact ID 11647734101 could not be used as a workflow run ID (404); no MP4 bytes retrieved.

## Required independent review after acquiring final MP4
Record exact file path, SHA-256, duration, dimensions, video/audio codecs, and independently observed timestamped samples at 00:00, 00:02, 00:05, 00:10, 00:15, 00:20, 00:25, 00:29 and final frame. Compare hook and each storyboard beat with the approved script; inspect continuous motion (not stills/Ken Burns), frozen/black tail, speech intelligibility, subtitles legibility and timing, audio-video synchronization, rights and originality. Only then set review booleans true with reviewer identity and concrete evidence.

## Free next action
Prefer the repository's `scripts/shorts_free_pipeline.py` with **licensed or original local moving clips** and verified narration/subtitle inputs. Pexels/Pixabay are potential asset sources, not pre-approved rights: verify each asset's license and any restrictions. Render a local MP4 and run ffprobe + full decode + frame/time observations; no payment or credits. Avoid claiming that the pipeline alone guarantees genuine moving footage or quality.

## Decision
No MP4 in hand; no timestamped observations can truthfully be asserted. `hook_storyboard_checked=false`, `moving_footage_checked=false`; ready=false. No publishing, no purchase, no paid regeneration.
