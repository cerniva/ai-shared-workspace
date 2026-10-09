# Shorts independent review schema: two new checks (2026-10-10)

Source reviewed: main scripts/shorts_preflight.py (f81103f), lines 24–30 gate mapping; lines 86–95 review identity and existing checks; lines 106–114 CLI --manifest; tests/test_preflight_manifest_gates.py lines 18–36. This is a schema specification, not implementation.

## JSON placement and types
Keep existing review JSON fields `sha256` (exact final MP4 SHA-256), `reviewer` (nonempty human/review-agent identity), and `checks` object. Add two **required boolean** entries inside `checks` when the corresponding manifest production_gate is true:
- `hook_storyboard_checked: true|false`
- `moving_footage_checked: true|false`
No truthy strings, missing/null or self-declared success. false/missing -> preflight ready=false with gate blocker. Do not store media, credentials or personal information in the review file.

## hook_storyboard_checked
**What:** Compare the approved hook and storyboard to the final full-duration MP4 and transcript/timecoded shot list: opening hook delivered in first seconds; story beats in intended order; spoken claims match visible scenes and captions; ending/reveal matches plan. A mere storyboard file, metadata flag or render success is insufficient. If any beat is missing, misleading or mismatched, false.
**Who:** Independent content reviewer (human or separate QC agent) who actually inspects the final MP4, storyboard and transcript, not the script that created the render. Reviewer records their identity and sha256.

## moving_footage_checked
**What:** Inspect the entire final MP4 (not only a thumbnail or first frames). Verify genuine temporally changing footage across intended shots; reject still-photo slideshows, Ken Burns zoom/pan on stills, frozen frames, black/missing visual tail, and repetitive static segments presented as moving footage. Motion analysis may assist, but requires visual review and duration coverage; reject false positives from subtitles/camera zoom only.
**Who:** Independent visual-QC reviewer or separate vision agent with access to the actual final MP4 and timestamps. The render pipeline must not mark its own output approved.

## Minimal review shape (illustrative, not verified)
```json
{
  "sha256": "<actual final MP4 sha256>",
  "reviewer": "independent-qc-identifier",
  "checks": {
    "hook_storyboard_checked": true,
    "moving_footage_checked": true
  }
}
```
Other existing required checks (rights_checked, speech_intelligible, audio_visual_sync, text_readable, facts_verified, correct_channel, duplicate_checked etc.) must remain; example is not a complete passing review.

## Grok acceptance
- Extend review JSON schema/producer with both boolean fields; independent reviewer must set them after checking final MP4.
- Wire --manifest in shorts-free-build and render workflows.
- Negative tests: missing/null/string/false, wrong MP4 sha256, self-approved render, storyboard mismatch, static slideshow, frozen tail, absent reviewer; positive: independent review with all gates and full decode.
- Real MP4 QA artifact + workflow run ID + main read-back required before marking done. No fake true defaults.
