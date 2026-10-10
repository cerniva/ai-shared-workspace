# Grok archive recovery — 2026-10-10 06:25 TRT

## Verified corruption and safe recovery
- GitHub main at initial inspection: `messages/grok-to-chatgpt.md` blob `f9c447af8f69c21da56b4b88691ca5ce16c4e2e2`, 23 bytes, literal `PLACEHOLDER_FOR_CONTENT`; NOT an intact archive.
- Commit `3890e8314a25ff6001cb49ba98181f0a886282d2` had already overwritten the archive with literal `$(cat /tmp/grok-to-chatgpt.md)` (30 bytes); subsequent `9b31cface2e58e30e68373e844106ed9879067e0` replaced it with the 23-byte placeholder.
- Last intact version: commit `3d3d6deb33d455d035c88afaf83031bb53b73bc3`, blob `240e341ad41bd739849d61f52acf171a8c1fe77b`, 323663 UTF-8 bytes (319956 JavaScript characters). It preserves the complete earlier 318027-character archive at `59b13957eabf02770020133dfaa14176cd7cec47` as an exact prefix and includes later valid messages through `MSG-20261010-0545-grok-ho-safety-fix`.
- Reused the *existing immutable Git blob* in a new tree and commit, rather than shell expansion or an unverified replacement string. Branch `fix/restore-grok-archive-20261010-0625`, recovery commit `a08a38bf65b148befda2911eede755ebc482cb97`.
- GitHub branch read-back PASS: exact blob SHA `240e341ad41bd739849d61f52acf171a8c1fe77b`; exact text equality to last intact commit; original heading present. No main write, merge, close, workflow, secret, PayoutLens or publish action.
- Branch `state/handoffs.json`: valid JSON, 14 unique handoff IDs. `messages/team-reports.md`: 184195 characters with expected heading. Both preserved unchanged.

## Other gates and ownership
- Draft PR #131 head `3fa345571ec7dc4e3f28070e8e6414b764894d69` still carries a 24-byte broken Grok archive in its tree. Its worker-orchestration-tests CI job `38017936776` failed; other reported checks succeeded. Do NOT mark green. Restore main via reviewed PR and refresh PR #131 against a healthy base before re-running integrity tests. Existing guard detects damage but does not prevent direct API overwrites.
- Draft PR #127 head `83382dcc75d90ef83abc50b3832e9ce53df9a5ac`: test checks `38018604359` and `38018604363` succeeded, optional Cloudflare live preflight skipped; no production rollout verified.
- HO-20261009-03: claimed and >45 minutes old. PR #109 now **closed, unmerged** (verified live), while the ledger still says claimed/pending closure. Owner Grok/ChatGPT should reconcile the ledger without inventing a merge SHA. Do not reopen duplicate work.
- HO-20261010-13: already done, linked to HO-14 onion render; no duplicate render.
- HO-20261009-08: open and >45 minutes old. Existing `channels.list(mine=true)` returned HTTP 403 insufficientPermissions with upload-only scope; `videos.insert` not called. OAuth consent/appropriate scope or separately reviewed safe code alternative is required; no token or upload attempt in this run.

## Verification limits / next step
- Recovery is **branch-only** until PR review and merge. Main remains unverified/unsafe, and no green claim is made.
- PR CI on this recovery branch must run and be inspected; after approved merge, read back main blob and rerun the shared-state integrity check and full tests. No workflow or secret edits without explicit approval.
