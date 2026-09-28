# Free-First Shorts Monetization Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the existing zero-credit Shorts renderer with free media acquisition, packet-to-render orchestration, dynamic monetization/engagement scoring, and a secret-safe manual build workflow that produces a technically validated MP4 without publishing it.

**Architecture:** Preserve the existing `shorts_research.py -> shorts_render.py -> shorts_preflight.py` chain. Add a small media-provider module for Pexels/Pixabay/Openverse and an orchestration module that turns an approved research packet into downloaded assets, provenance metadata, captions, and the existing render manifest. Keep the current secret-free `shorts-free-render.yml` unchanged; add a separate secret-using `shorts-free-build.yml` for acquisition + render + preflight so provider secrets never leak into manifests or logs.

**Tech Stack:** Python 3 stdlib (`urllib`, `json`, `pathlib`, `unittest.mock`), FFmpeg/ffprobe, eSpeak NG, GitHub Actions, existing Shorts research/preflight/upload code.

**Spec:** `docs/superpowers/specs/2026-09-28-free-first-shorts-monetization-engine-design.md`

## Global Constraints

- PayoutLens is out of scope and must not be modified.
- Keep `scripts/shorts_preflight.py`, `scripts/youtube_upload.py`, `.github/workflows/youtube-upload.yml`, duplicate-prevention rules, and fail-closed publication behavior intact.
- Read `PEXELS_API_KEY` and `PIXABAY_API_KEY` only from environment/GitHub Actions secrets; never hard-code or print them.
- Default production path consumes zero paid generative-video credits.
- Paid generators remain fallback only; this plan does not add or invoke them.
- Publication is not part of the new build workflow; a produced MP4 still needs existing independent review before any upload.
- Topic, format, and language remain dynamic; no permanent kitchen, finance, Turkish, English, or other niche priority.
- Use TDD: add the failing test first, verify the expected failure, implement the smallest passing change, rerun tests, then commit.
- Existing zero-credit FFmpeg + eSpeak implementation from commits `a2e99c2e` and `94488d09` is baseline infrastructure, not work to duplicate.

## Review Focus

1. **Only one provider secret exists:** Pexels missing or Pixabay missing must fall through to the remaining configured provider without exposing a credential; pin in `tests/test_shorts_media.py`.
2. **Provider response is malformed or empty:** a bad upstream payload must be skipped/fail clearly and never create a bogus asset path; pin in `tests/test_shorts_media.py`.
3. **Packet asks for free render but lacks language/narration/media queries:** gate must fail before network or render; pin in `tests/test_shorts_research_free_render.py`.
4. **Turkish/foreign-language packet:** narration voice and captions must follow the packet language rather than silently defaulting to English; pin in `tests/test_shorts_free_pipeline.py`.
5. **Secret-bearing URL/error text:** `PIXABAY_API_KEY` must be redacted from raised errors/loggable strings; pin in `tests/test_shorts_media.py`.

---

## File Structure

**Create**
- `scripts/shorts_media.py` — Pexels/Pixabay/Openverse search, normalized asset schema, downloads, secret redaction.
- `scripts/shorts_free_pipeline.py` — approved packet -> media queries -> local assets/provenance -> captions/render manifest -> existing renderer.
- `tests/test_shorts_media.py` — provider normalization, fallback, malformed payloads, redaction, download behavior.
- `tests/test_shorts_research_free_render.py` — backward-compatible dynamic scoring and extra gate fields only when free render is requested.
- `tests/test_shorts_free_pipeline.py` — packet orchestration, language/voice, captions, provenance, no-network unit path.
- `tests/test_shorts_free_build_workflow.py` — workflow safety and secret wiring.
- `tests/test_shorts_sop_policy.py` — policy regression for dynamic topic/language and free-first wording.
- `.github/workflows/shorts-free-build.yml` — manual secret-using acquisition/render/preflight workflow; never publishes.

**Modify**
- `scripts/shorts_research.py` — optional monetization/engagement/cost/right-safety scoring and conditional free-render packet requirements.
- `.github/workflows/shorts-render-tests.yml` — include new modules/tests/workflow paths and run their tests.
- `research/youtube/SHORTS_SOP.md` — remove fixed kitchen priority and HeyGen/ElevenLabs-first production wording; document free-first path.
- `knowledge/shorts/RESEARCH_MODULE.md` — document free-first acquisition/render after gate while preserving existing gate/preflight semantics.

**Do not modify**
- `scripts/shorts_preflight.py`
- `scripts/youtube_upload.py`
- `.github/workflows/youtube-upload.yml`
- `.github/workflows/shorts-free-render.yml` except only if an implementation-time regression proves a strictly necessary compatibility fix; otherwise leave it secret-free.
- any PayoutLens path

---

### Task 1: Add normalized free-media providers with safe fallback

**Files:**
- Create: `scripts/shorts_media.py`
- Create: `tests/test_shorts_media.py`

**Interfaces:**
- Produces: `search_pexels(query: str, api_key: str, *, limit: int = 12) -> list[dict]`
- Produces: `search_pixabay(query: str, api_key: str, *, limit: int = 12) -> list[dict]`
- Produces: `search_openverse(query: str, *, limit: int = 12) -> list[dict]`
- Produces: `search_free_media(query: str, *, env: Mapping[str, str] | None = None, limit: int = 12) -> list[dict]`
- Produces: `download_asset(asset: dict, destination: Path) -> Path`
- Produces asset schema keys: `provider`, `provider_asset_id`, `source_url`, `download_url`, `media_type`, `license_note`, `creator`, `retrieved_at`.
- Provider order: configured Pexels -> configured Pixabay -> Openverse. Missing secret means skip that provider; it is not a fatal error if another provider succeeds.

- [ ] **Step 1: Write provider normalization/fallback/redaction tests**

Add tests named:
- `test_pexels_video_response_normalizes_to_media_asset`
- `test_pixabay_video_response_normalizes_to_media_asset`
- `test_openverse_result_requires_explicit_license_and_normalizes`
- `test_missing_pexels_key_falls_back_to_pixabay`
- `test_missing_both_keys_falls_back_to_openverse`
- `test_empty_or_malformed_provider_payload_does_not_create_asset`
- `test_pixabay_key_is_redacted_from_error_text`
- `test_download_asset_rejects_non_http_url`

Use `unittest.mock.patch` around the module's private JSON/download request helpers; tests must not call the live internet.

- [ ] **Step 2: Run tests to verify expected failure**

Run: `python3 -m unittest tests.test_shorts_media -v`
Expected: FAIL because `scripts.shorts_media` and the listed functions do not exist.

- [ ] **Step 3: Implement `scripts/shorts_media.py` with stdlib HTTP only**

Use `urllib.request` with bounded timeouts. Pexels authentication goes in the `Authorization` header. Pixabay uses its documented `key` query parameter, but all exceptions/loggable URLs must pass through `_redact_url(url: str) -> str` before being surfaced. Openverse results must be discarded when license/license URL metadata is absent. Return normalized dictionaries only; never include API keys or request headers in them.

- [ ] **Step 4: Run media tests**

Run: `python3 -m unittest tests.test_shorts_media -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/shorts_media.py tests/test_shorts_media.py
git commit -m "feat: add free Shorts media providers"
```

---

### Task 2: Extend research scoring and gate only for free-render packets

**Files:**
- Modify: `scripts/shorts_research.py`
- Create: `tests/test_shorts_research_free_render.py`

**Interfaces:**
- Existing `score_item(item: dict) -> dict` remains callable.
- Existing `gate_packet(packet: dict) -> list[str]` remains callable.
- Add optional score dimensions with neutral default `5.0`: `monetization`, `engagement`, `low_production_cost`, `rights_safety`, `language_fit`.
- Preserve all existing required criteria and veto behavior.
- When `packet["free_render_requested"] is True`, additionally require non-empty `language`, `content_type`, `narration_text`, and `media_queries` (list of non-empty strings).
- Legacy packets without `free_render_requested` keep their current gate requirements and do not gain new blockers.

- [ ] **Step 1: Write backward-compatibility and dynamic-score tests**

Add tests named:
- `test_legacy_candidate_without_optional_dimensions_keeps_neutral_score`
- `test_equal_base_candidate_with_better_monetization_engagement_and_cost_ranks_higher`
- `test_legacy_packet_does_not_require_free_render_fields`
- `test_free_render_packet_requires_language_content_type_narration_and_queries`
- `test_free_render_packet_accepts_turkish_or_english_language_string`

- [ ] **Step 2: Run tests to verify expected failure**

Run: `python3 -m unittest tests.test_shorts_research_free_render -v`
Expected: FAIL on missing optional dimensions/free-render conditional gate behavior.

- [ ] **Step 3: Implement the minimum compatible scoring/gate change**

Keep existing `CRITERIA` semantics; add a separate optional-dimension list so old candidates do not receive zeroes for fields that did not exist. Add the optional values to `total` using `5.0` when omitted. Add conditional free-render blockers without changing legacy packet requirements.

- [ ] **Step 4: Run focused and existing research tests**

Run: `python3 -m unittest tests.test_shorts_research_free_render -v`
Expected: PASS.

Run: `python3 scripts/shorts_research.py gate --packet knowledge/shorts/packets/$(ls knowledge/shorts/packets | head -n 1)` if at least one packet exists; otherwise skip with an explicit note rather than fabricating a fixture in the repository.
Expected: Existing packet behavior unchanged.

- [ ] **Step 5: Commit**

```bash
git add scripts/shorts_research.py tests/test_shorts_research_free_render.py
git commit -m "feat: score Shorts for monetization and free production"
```

---

### Task 3: Build approved packets into local render inputs

**Files:**
- Create: `scripts/shorts_free_pipeline.py`
- Create: `tests/test_shorts_free_pipeline.py`

**Interfaces:**
- Consumes: `gate_packet(packet: dict) -> list[str]` from Task 2.
- Consumes: `search_free_media(...)` and `download_asset(...)` from Task 1.
- Consumes: existing `scripts.shorts_render.render(manifest_path: Path, output_path: Path) -> dict`.
- Produces: `default_espeak_voice(language: str, explicit_voice: str | None = None) -> str`.
- Produces: `build_srt(text: str, target_seconds: float, *, max_chars: int = 42) -> str`.
- Produces: `prepare_render_bundle(packet_path: Path, workdir: Path, *, env: Mapping[str, str] | None = None) -> dict` returning paths for `render_manifest`, `provenance`, `captions`, and downloaded `assets`.
- Produces CLI: `python3 scripts/shorts_free_pipeline.py PACKET WORKDIR OUTPUT_MP4` which prepares the bundle then calls existing `render()`; it does not publish.

- [ ] **Step 1: Write orchestration tests without live network**

Add tests named:
- `test_pipeline_refuses_packet_that_fails_research_gate`
- `test_pipeline_uses_media_queries_in_order_and_deduplicates_assets`
- `test_pipeline_writes_provenance_without_secrets`
- `test_turkish_packet_defaults_to_tr_voice`
- `test_english_packet_defaults_to_en_us_voice`
- `test_unknown_language_requires_explicit_narration_voice`
- `test_build_srt_uses_mobile_readable_chunks_and_packet_language_text`
- `test_render_manifest_contains_local_paths_only`

Mock `search_free_media`, `download_asset`, and `render`; unit tests must not spend credits, hit APIs, or require FFmpeg.

- [ ] **Step 2: Run tests to verify expected failure**

Run: `python3 -m unittest tests.test_shorts_free_pipeline -v`
Expected: FAIL because `scripts.shorts_free_pipeline` does not exist.

- [ ] **Step 3: Implement bundle preparation and CLI**

Rules:
- Call `gate_packet` before any provider request.
- Use at most 3 unique visual assets per Short initially (YAGNI; renderer already loops video).
- Split `target_seconds` evenly across selected visuals, with the final segment receiving floating-point remainder.
- Write `captions.srt` from `narration_text` using `build_srt`.
- Voice defaults: language beginning `tr` -> `tr`; beginning `en` -> `en-us`; any other language requires packet field `narration_voice` until a validated local voice mapping is added.
- Write `provenance.json` with normalized asset records only; never environment values.
- Build a manifest compatible with current `shorts_render.py` using `narration_text`, `narration_voice`, `visuals`, `subtitles`, and `target_seconds`.

- [ ] **Step 4: Run pipeline tests**

Run: `python3 -m unittest tests.test_shorts_free_pipeline -v`
Expected: PASS.

- [ ] **Step 5: Run existing renderer regression tests**

Run: `python3 -m unittest tests.test_shorts_render tests.test_shorts_render_tts -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/shorts_free_pipeline.py tests/test_shorts_free_pipeline.py
git commit -m "feat: prepare free Shorts render bundles"
```

---

### Task 4: Add a secret-safe manual acquisition + render workflow

**Files:**
- Create: `.github/workflows/shorts-free-build.yml`
- Create: `tests/test_shorts_free_build_workflow.py`
- Modify: `.github/workflows/shorts-render-tests.yml`

**Interfaces:**
- Workflow inputs: `packet_path` (required repository-relative path) and `output_name` (default `short.mp4`).
- Workflow secrets: `PEXELS_API_KEY`, `PIXABAY_API_KEY` exposed only as environment variables to the pipeline step.
- Workflow outputs as artifact files: MP4, `preflight.json`, `provenance.json`, `captions.srt`, render manifest.
- Workflow never calls `youtube_upload.py`, Metricool, Buffer, or any paid video provider.

- [ ] **Step 1: Write workflow policy tests**

Add tests named:
- `test_build_workflow_uses_both_provider_secrets_without_echoing_values`
- `test_build_workflow_calls_free_pipeline_and_preflight`
- `test_build_workflow_uploads_mp4_preflight_and_provenance_artifacts`
- `test_build_workflow_never_publishes_or_calls_paid_generators`
- `test_existing_secret_free_render_workflow_remains_secret_free`

- [ ] **Step 2: Run tests to verify expected failure**

Run: `python3 -m unittest tests.test_shorts_free_build_workflow tests.test_shorts_free_render_workflow -v`
Expected: FAIL because `shorts-free-build.yml` does not exist; existing secret-free workflow test remains PASS.

- [ ] **Step 3: Implement `.github/workflows/shorts-free-build.yml`**

Use `workflow_dispatch`, `permissions: contents: read`, checkout, install `ffmpeg espeak-ng`, validate `packet_path`/`output_name` against path traversal, run the free pipeline with secret env vars, then run existing `shorts_preflight.py`. Treat `independent_review_missing` as the one expected nontechnical blocker for artifact creation, but fail on all other preflight blockers. Upload the artifact bundle for 7 days. Do not add any upload/publish step.

- [ ] **Step 4: Expand renderer CI path filters/tests**

Add new scripts, tests, and workflow paths to `.github/workflows/shorts-render-tests.yml`, and include the new unittest modules in its renderer-test command before the full `pytest -q` step.

- [ ] **Step 5: Run workflow tests**

Run: `python3 -m unittest tests.test_shorts_free_build_workflow tests.test_shorts_free_render_workflow -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/shorts-free-build.yml .github/workflows/shorts-render-tests.yml tests/test_shorts_free_build_workflow.py
git commit -m "ci: add free Shorts acquisition build workflow"
```

---

### Task 5: Update Shorts operating policy without removing existing safety gates

**Files:**
- Modify: `research/youtube/SHORTS_SOP.md`
- Modify: `knowledge/shorts/RESEARCH_MODULE.md`
- Create: `tests/test_shorts_sop_policy.py`

**Interfaces:**
- Documentation must describe dynamic topic/format/language selection based on monetization + engagement + retention + rights + cost.
- Documentation must name free-first acquisition/render as the default once verified.
- Documentation must preserve research gate -> render -> preflight -> review -> publication separation.

- [ ] **Step 1: Write policy regression tests**

Assertions:
- `SHORTS_SOP.md` no longer contains `Mutfak hattı öncelikli`.
- It no longer presents `HeyGen grafik / ElevenLabs` as the primary production step.
- It contains `free-first` (case-insensitive), Pexels, Pixabay, FFmpeg, and the rule that language/topic are dynamic.
- `RESEARCH_MODULE.md` keeps `scripts/shorts_preflight.py` and `scripts/youtube_upload.py` protection text and documents paid render as fallback rather than default.

- [ ] **Step 2: Run test to verify expected failure**

Run: `python3 -m unittest tests.test_shorts_sop_policy -v`
Expected: FAIL against current fixed-kitchen/paid-first wording.

- [ ] **Step 3: Make the smallest documentation changes**

Do not rewrite the documents wholesale. Replace only the obsolete topic/production policy and add the new free-first path/fallback wording.

- [ ] **Step 4: Run policy test**

Run: `python3 -m unittest tests.test_shorts_sop_policy -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add research/youtube/SHORTS_SOP.md knowledge/shorts/RESEARCH_MODULE.md tests/test_shorts_sop_policy.py
git commit -m "docs: make Shorts strategy dynamic and free-first"
```

---

### Task 6: Verify locally, in CI, and with one real secret-backed smoke build

**Files:**
- No new production files expected.
- Modify only tests/workflow if verification reveals a real defect; follow TDD for any fix.

**Interfaces:**
- Consumes all Tasks 1-5.
- Produces evidence that the branch is safe to make the free-first path the default producer.

- [ ] **Step 1: Run all focused Shorts tests**

Run:
```bash
python3 -m unittest \
  tests.test_shorts_media \
  tests.test_shorts_research_free_render \
  tests.test_shorts_free_pipeline \
  tests.test_shorts_render \
  tests.test_shorts_render_tts \
  tests.test_shorts_free_render_workflow \
  tests.test_shorts_free_build_workflow \
  tests.test_shorts_sop_policy -v
```
Expected: PASS.

- [ ] **Step 2: Run full Python suite and compile checks**

Run:
```bash
python3 -m pytest -q
python3 -m py_compile scripts/shorts_media.py scripts/shorts_free_pipeline.py scripts/shorts_research.py scripts/shorts_render.py scripts/shorts_preflight.py
```
Expected: all tests PASS; compile exits 0.

- [ ] **Step 3: Confirm protected scope**

Run: `git diff --name-only <base>...HEAD`
Expected: no PayoutLens paths; no change to YouTube upload code/workflow; no secret values committed.

Run: `git grep -nE '(PEXELS_API_KEY|PIXABAY_API_KEY).{0,20}[A-Za-z0-9_-]{20,}' -- ':!docs/superpowers/plans/*'`
Expected: only variable/secret names and workflow references, never literal secret values.

- [ ] **Step 4: Push branch and wait for CI**

Expected: Shorts renderer tests, full Python suite, and security/code-quality checks all green. Do not claim completion from local tests alone.

- [ ] **Step 5: Dispatch one real `shorts-free-build` smoke run using a purpose-built test packet**

Create the test packet on the implementation branch with `free_render_requested: true`, at least two factual sources, `rights_ok: true`, explicit `language`, `content_type`, short `narration_text`, 1-2 `media_queries`, and all existing gate checklist fields true. Use a non-sensitive evergreen topic; do not publish the result.

Expected workflow evidence:
- at least one of Pexels/Pixabay returns usable media, with Openverse available as no-key fallback;
- artifact contains real MP4 + `preflight.json` + `provenance.json` + captions/render manifest;
- MP4 is 1080x1920, H.264 + AAC, fully decodable, and has detectable audio signal;
- technical preflight has no blockers other than `independent_review_missing`;
- logs/manifests contain no API key values.

- [ ] **Step 6: Remove the temporary smoke packet if it has no lasting research value, or keep it under an explicit fixture path if tests depend on it**

Expected: no accidental production candidate is left looking publish-ready.

- [ ] **Step 7: Final commit if verification required fixture/docs changes**

```bash
git add <only verified required files>
git commit -m "test: verify free Shorts pipeline end to end"
```

---

## Deferred Quality Upgrades (not blockers for this plan)

- **Kokoro/Piper:** evaluate as a separate voice-quality plan after this pipeline works end to end. The repo already has zero-credit eSpeak NG narration, so adding heavyweight TTS dependencies now would increase failure surface before media acquisition is proven.
- **Remotion:** optional richer template/animation layer after FFmpeg-first acquisition/render is stable. The current renderer already satisfies the zero-credit deterministic output requirement.
- **Whisper:** add only where caption timing/intelligibility QA produces measurable benefit; known narration text does not need re-transcription on every run.

These are deliberately deferred by YAGNI, not rejected.

## Self-Review Result

- **Spec coverage:** free media acquisition, secret handling, dynamic topic/language scoring, local narration, captions, FFmpeg render, existing preflight, fail-closed publication separation, analytics-oriented scoring, and PayoutLens protection are covered. Paid fallback remains available but is not modified.
- **Current-state correction:** the design spec predated commits that already added FFmpeg rendering and eSpeak NG narration. This plan reuses those verified components instead of rebuilding them.
- **Type consistency:** Task 3 consumes the exact Task 1 and Task 2 interfaces defined above and the existing `render(Path, Path) -> dict` interface.
- **Review Focus:** all five listed failure classes have explicit owning tests.
- **Proportion:** tasks are limited to remaining missing integration; optional Remotion/Kokoro/Piper/Whisper work is deferred rather than inflating this implementation.
