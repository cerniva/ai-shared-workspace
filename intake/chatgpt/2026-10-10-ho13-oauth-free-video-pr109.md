# HO-20261010-13 — ChatGPT handoff (2026-10-10)

id: HO-20261010-13
from: chatgpt
to: grok
intent: handoff
status: prepared_not_executed
evidence: scripts/shorts_free_pipeline.py; .github/workflows/shorts-free-build.yml; scripts/youtube_upload.py; PR #109

## 1. YouTube OAuth: secure preparation, no secrets in repo/chat
- Console project: https://console.cloud.google.com/projectselector2/home/dashboard
- Enable API: https://console.cloud.google.com/apis/library/youtube.googleapis.com
- OAuth branding/audience/test users: https://console.cloud.google.com/auth/overview
- OAuth client configuration: https://console.cloud.google.com/auth/clients
- GitHub Actions secrets: https://github.com/cerniva/ai-shared-workspace/settings/secrets/actions
- Choose correct Cloud project, enable YouTube Data API v3; configure consent app and user audience; add authorized channel owner's Google account as test user when testing is applicable.
- Create/reuse a suitable OAuth client **matching the actual token exchange callback** (desktop/loopback for local flow, web application with exact registered HTTPS redirect for server flow). Do not invent redirect URI.
- Request minimum upload scope https://www.googleapis.com/auth/youtube.upload ; offline access for refresh token. Confirm correct YouTube channel and scope.
- Store YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN only as GitHub Actions secrets; never paste into chats, issues, files or CI logs. Existing script requires all three. Refresh token must be issued to same client; invalid_grant requires fresh authorized token.
- Manual actions for Furkan: (1) sign in/select Cloud project, (2) enable API if disabled, (3) approve branding/audience/test-user settings, (4) create/authorize OAuth client with verified callback, (5) approve consent for correct YouTube channel, (6) privately set three GitHub Actions secrets. ChatGPT cannot click consent or verify secrets' values. After this Grok runs non-publishing auth/dry-run checks; publish requires separate approval.
- Official docs: https://developers.google.com/youtube/v3/guides/auth/server-side-web-apps and https://developers.google.com/youtube/v3/guides/auth/installed-apps

## 2. Free MP4 — exact existing workflow invocation
Verified on main: `.github/workflows/shorts-free-build.yml` has `workflow_dispatch` inputs `packet_path` (required repository-relative existing JSON), `output_name` (optional, default short.mp4). Workflow installs ffmpeg/espeak-ng, loads plan learnings and runs:
```bash
python3 scripts/plan_learnings.py video_shopify --require --out artifacts/plan_learnings.json
python3 scripts/shorts_free_pipeline.py "$PACKET" artifacts/bundle "artifacts/$OUTPUT_NAME" --learnings artifacts/plan_learnings.json
python3 scripts/shorts_preflight.py "artifacts/$OUTPUT_NAME" --manifest artifacts/bundle/render.json > artifacts/preflight.json
```
Grok trigger (after selecting a **validated, approved packet JSON path** on main):
```bash
gh workflow run shorts-free-build.yml --repo cerniva/ai-shared-workspace --ref main -f packet_path='<APPROVED_REPO_RELATIVE_PACKET>.json' -f output_name='short-ho13.mp4'
```
Alternative Actions UI: https://github.com/cerniva/ai-shared-workspace/actions/workflows/shorts-free-build.yml → Run workflow → main → packet_path + output_name → Run workflow.
**Do not trigger using a guessed packet path.** Confirm packet's gate_packet validation, license, real moving footage, approved hook/storyboard, narration/caption alignment and no cost before triggering. `tests/fixtures/shorts_real_smoke_ice_float.json` exists as a test fixture, NOT an approved onion production packet; do not silently substitute. API keys PEXELS_API_KEY / PIXABAY_API_KEY may be needed for free media acquisition; absence can block. eSpeak-ng synthetic voice may not meet natural-voice QC; no fabricated approval. Render artifact != upload permission. No purchase, no YouTube publish.
- Status: workflow/command prepared for Grok; **not triggered**; MP4 not claimed.

## 3. Furkan's one-step per app
- Claude: https://claude.ai/new → connect GitHub if available or upload a safe code-review bundle, then send assigned APP-CLAUDE-20261010-01 message.
- Gemini: https://gemini.google.com/app → import/share accessible code context or paste task, then send APP-GEMINI-20261010-01.
- Manus: https://manus.im/app → authorize a functioning My Browser/GitHub session, then resume APP-MANUS-20261010-01 (current browser connection blocked).
- Lindy: https://www.lindy.ai/ → connect Gmail/GitHub with least privilege, then resume APP-LINDY-20261010-01; no mail sends or calendar changes without explicit Furkan approval.

## 4. PR #109 close recommendation ONLY
https://github.com/cerniva/ai-shared-workspace/pull/109
Search result describes PR #109 as **Draft**, preserving optional plan_tags/status/use_count/cycle metadata, with pending tests and promotion affected_plans mapping; handoffs.json notes head 6323990, 60+ commits behind and claimed content already in main. **Recommend close without merge only after Grok compares PR head to current main and confirms every desired change is already present and tested**. If metadata preservation or affected_plans mapping is still missing, do NOT close as complete; split the missing work into a fresh focused PR with tests/read-back, then close stale #109 as superseded with cross-link. Closing PR is not authorized here; no action taken.

## Proof / limits
All commands above were derived from repository source. OAuth account/secret presence, approved packet path, real render success and PR diff equivalence were NOT verified. No workflow triggered, no purchase, no publish, no secret recorded. PayoutLens untouched.
