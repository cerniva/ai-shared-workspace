# Free-First Shorts Monetization Engine — Design

Date: 2026-09-28
Status: Proposed design, awaiting user review
Owner scope: `cerniva/ai-shared-workspace`
Protected scope: PayoutLens is out of scope and must not be modified.

## 1. Goal

Build a Shorts production path that minimizes paid AI credits while maximizing the chance of useful business outcomes: views, retention, engagement, subscriber conversion, and monetization potential.

The system must not lock itself to one topic, niche, or language. Turkish, English, or another supported language is a candidate attribute, not the objective. Topic, format, and language are chosen per video based on evidence and channel learning.

## 2. Success criteria

A successful implementation should:

1. Keep the existing research, packet gate, preflight, upload, and decision-log concepts intact.
2. Replace paid-render-first behavior with a free-first production path.
3. Use `PEXELS_API_KEY` and `PIXABAY_API_KEY` only from environment/secrets; never hard-code or print them.
4. Produce a real portrait MP4 with audible speech when a voiced format is selected.
5. Preserve the existing fail-closed `scripts/shorts_preflight.py` behavior.
6. Avoid duplicate upload/render attempts after timeouts until remote state is checked.
7. Allow paid tools only as explicit fallback when the free-first route cannot satisfy the packet.
8. Record enough metadata to learn which topic/format/language combinations perform best.
9. Touch no PayoutLens files.

## 3. Existing system to preserve

Current Shorts flow already defines:

`research -> candidate pool -> score -> select -> verify -> original angle -> hook -> script -> visual/audio plan -> gate -> render -> preflight -> queue/publish -> performance log`

Protected existing components:

- `scripts/shorts_preflight.py`
- `scripts/youtube_upload.py`
- `.github/workflows/youtube-upload.yml`
- `knowledge/shorts/RESEARCH_MODULE.md` flow and gate semantics
- duplicate-prevention rules
- fail-closed publication behavior

The current `research/youtube/SHORTS_SOP.md` still contains two outdated assumptions that the implementation should revise after this design is approved:

- fixed kitchen-topic priority
- HeyGen/ElevenLabs as the primary production path

## 4. Recommended architecture

Use a hybrid renderer with FFmpeg as the mandatory low-cost core and Remotion as an optional template/animation layer.

### 4.1 Why this approach

FFmpeg is the most dependable base for stitching clips, fitting 9:16, mixing narration/music, burning captions, validating codecs, and producing deterministic H.264/AAC output. Remotion adds richer reusable motion templates but should not be mandatory for every video because Chromium/Node rendering is heavier.

Therefore:

- Simple Short: media + narration + captions + basic transitions -> FFmpeg only.
- Rich template Short: optional Remotion composition -> FFmpeg final normalization/preflight input.
- Paid AI video generation: fallback only.

## 5. Pipeline

### Stage A — Opportunity ranking

Before render, compare multiple candidates across:

- demand / trend strength
- competition / saturation
- hook strength
- expected retention
- comment/share/rewatch potential
- subscriber-conversion potential
- monetization/commercial potential
- originality / differentiation
- factual confidence
- copyright/policy risk
- production feasibility
- expected production cost
- historical Cerno performance, when available

No single topic or language is permanently preferred.

### Stage B — Media acquisition

Primary sources:

1. Pexels API using `PEXELS_API_KEY`
2. Pixabay API using `PIXABAY_API_KEY`
3. Openverse for license-discoverable media where appropriate
4. explicitly verified public/first-party sources for topic-specific material

For every selected asset, store source metadata sufficient to review provenance and rights assumptions.

Do not download or use an asset if licensing/provenance is unclear for the intended use.

### Stage C — Narration

Free-first narration order:

1. Local/open TTS suitable for the selected language.
2. Kokoro for supported languages where voice quality is acceptable.
3. Piper or another validated local engine for languages/voices Kokoro does not cover well.
4. Existing paid TTS only as fallback.

Narration output must be a real audio file, not merely a script field.

### Stage D — Captions and audio QA

Use the known narration text to build captions. Whisper or another local speech recognizer may be used as a QA/fallback tool when timing or intelligibility needs verification; it is not required to transcribe known text on every run.

Checks before render completion:

- speech exists when voice is expected
- narration is intelligible
- caption text matches selected language
- caption timing is plausible
- music does not overpower speech

### Stage E — Render

Target output:

- portrait 9:16
- H.264 video
- AAC audio
- mobile-readable captions
- deterministic file path and job ID
- complete decode

FFmpeg is responsible for final normalized output even when Remotion is used upstream.

### Stage F — Existing gate and publication path

The render must pass the existing preflight and independent review requirements before publication.

Publication remains separate from production:

- use the verified YouTube path when it works
- use the already-authorized Metricool fallback when appropriate
- never upload the same video twice because of an ambiguous timeout

## 6. Proposed repository components

Exact filenames may be refined during implementation planning, but responsibilities should remain separated.

Suggested modules:

- `scripts/shorts_media.py`
  - Pexels/Pixabay/Openverse search
  - normalized result schema
  - download with provenance metadata

- `scripts/shorts_tts.py`
  - language/voice selection
  - local TTS invocation
  - fallback policy

- `scripts/shorts_render.py`
  - FFmpeg-first assembly
  - optional Remotion invocation
  - captions/audio/music composition
  - output manifest

- `scripts/shorts_free_pipeline.py`
  - orchestration only
  - calls research packet gate before acquisition/render
  - calls existing preflight after render

- `tests/`
  - media normalization tests
  - TTS selection/fallback tests
  - render command tests
  - silent-audio rejection test
  - secret-redaction test
  - existing behavior regression tests

Do not merge these responsibilities into `youtube_upload.py`.

## 7. Data contracts

### 7.1 Media asset

```json
{
  "provider": "pexels|pixabay|openverse|other",
  "provider_asset_id": "string",
  "source_url": "string",
  "download_url": "string",
  "media_type": "video|image|audio",
  "license_note": "string",
  "creator": "string|null",
  "retrieved_at": "ISO-8601"
}
```

### 7.2 Render manifest

```json
{
  "job_id": "string",
  "packet_id": "string",
  "language": "string",
  "content_type": "string",
  "renderer": "ffmpeg|remotion+ffmpeg",
  "tts_engine": "string",
  "media_assets": [],
  "output_mp4": "string",
  "duration_seconds": 0,
  "has_voice": true,
  "captions": true,
  "created_at": "ISO-8601"
}
```

Secrets must never appear in either contract.

## 8. Failure and fallback behavior

### Missing API secret

- Do not crash the entire research system.
- Mark only that provider unavailable.
- Try the next configured free provider.
- If no legal media source remains, stop before render with a clear blocker.

### Provider rate limit / transient error

- bounded retry with backoff
- then fallback to another provider
- no infinite retry loop

### TTS failure

- try another local engine/voice compatible with the selected language
- if no acceptable free engine is available, stop or request paid fallback according to policy
- never silently publish a voiced-format Short without speech

### Render timeout

- inspect output/job state before rerunning
- never create duplicate publication attempts blindly

### Preflight failure

- fail closed
- record the exact reason
- do not publish

## 9. Security

- Read `PEXELS_API_KEY` and `PIXABAY_API_KEY` from GitHub Actions secrets/environment only.
- Never log secret values, request headers containing them, or full authenticated URLs.
- Redact provider credentials from error output.
- No API key is committed to repository files.
- Existing YouTube/Metricool credentials remain untouched.

## 10. Cost policy

Default path must consume zero paid generative-video credits.

Allowed by default:

- Pexels/Pixabay/Openverse within their free terms/quotas
- FFmpeg
- Remotion where its license permits this use
- local/open TTS
- Whisper/local QA
- GitHub Actions within available quota

Paid generators such as HeyGen, Runway, Higgsfield, OpenArt, ElevenLabs or equivalent are fallback only and must not be silently selected as the primary renderer.

## 11. Analytics learning loop

After enough data exists, record per-video:

- topic/archetype
- format
- language
- hook type
- duration
- engaged views
- chose-to-view / swipe-away when available
- average watch time
- retention
- rewatch signals when available
- likes/comments/shares
- subscriber conversion
- revenue/monetization signal when available

Do not declare a permanent winner from one video or a very small early sample. Use these fields to adjust future candidate scores.

## 12. Migration strategy

1. Add free-first modules without deleting the existing paid-render path.
2. Add tests before behavior changes.
3. Update Shorts SOP to remove fixed kitchen priority and paid-tool-first wording.
4. Add a free-first workflow/entry point behind explicit invocation at first.
5. Run smoke tests and existing preflight.
6. Only after verified success, make free-first the default renderer.
7. Keep paid render available as fallback.

This prevents a large-bang rewrite and preserves current upload/preflight behavior.

## 13. Verification plan

Implementation should demonstrate:

1. Tests fail first for the new expected behavior, then pass after implementation.
2. Pexels provider works with `PEXELS_API_KEY` present.
3. Pixabay fallback works with `PIXABAY_API_KEY` present.
4. Missing one provider key still allows the other provider to work.
5. A generated sample MP4 is 9:16, H.264, AAC, and fully decodable.
6. A deliberately silent voiced-format video is rejected.
7. Existing `shorts_preflight.py` remains the final media gate.
8. No secret appears in logs or manifests.
9. Existing upload behavior is unchanged unless a separately reviewed publication change is required.
10. No PayoutLens file changes appear in the diff.

## 14. Non-goals

This design does not:

- guarantee monetization or virality
- bypass YouTube policies
- auto-spend money or credits
- rewrite the existing worker architecture
- modify PayoutLens
- force every video to use Remotion
- force one language, topic, or niche

## 15. Decision summary

Adopt a free-first, dynamic Shorts production subsystem with:

`opportunity ranking -> free licensed media -> local/open TTS -> FFmpeg-first render -> optional Remotion -> existing preflight -> existing authorized publication path -> analytics learning`

This is the preferred architecture because it reduces recurring credit dependency while preserving the proven fail-closed parts of the current pipeline.
