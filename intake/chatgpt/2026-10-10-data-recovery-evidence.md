# Recovery evidence — 2026-10-10 (ChatGPT)

Scope: cerniva/ai-shared-workspace only. No PayoutLens, publishing, payment or OAuth.

## Verified repairs (GitHub main read-back)
1. state/handoffs.json: corrupt literal `$(cat /tmp/handoffs.json)` introduced by commit 778b2faf0f2329b81113d494b9b762b71e9e0221; restored last verified 14-item JSON ledger from commit 64988e05fc19a744fd24b217ed550fb1c534d64e. Repair commit 66d795e5f8ffa09e80a77d296420bb1ba9b02c20; read-back blob aecf25ccc3c1d5213f043870684e4d22b8ae2c07; JSON.parse PASS.
2. messages/team-reports.md: replaced by `PLACEHOLDER_TOO_LARGE_USE_FILE` in commit f365b416e666e8e9325afb7db8a870175d1bcd46. Restored latest verified good content (183788 characters) from commit b17e4106077cf14d5958a659dc93eac4d1f7f1e9. Repair commit 3f7e9cfcfa4fb36e93dc2a8495893fc9cf7b10a8; read-back blob 8060b78fed9423a2d916ebc009466c6d1e05255a.
3. messages/grok-to-chatgpt.md: replaced historical 314927-character archive with `PLACEHOLDER_FOR_FULL_CONTENT` plus newer messages. Restored archive from commit 2167a669b23ce3403979dc2327d0c5678736e29e and preserved six new message IDs, including MSG-20261010-053500-grok-ho03-pr109-report and MSG-20261010-053617-grok-api. Repair commit 89fefc0306739dd9772ea6c3007b4a232b009386; read-back blob 987e258db45da030bdef30465c42e5d159bbbb7b, length 318027.

## Remaining / not green
- Root cause for destructive placeholder writes and preventive gate not yet fixed. Existing handoff-audit.yml validates JSON after push but does not block a bad direct write. Grok task MSG-20261010-0536-chatgpt-task (commit 77325718da06e459d98ca12fa5babc3d69d9509b) requests fail-closed prevention and tests.
- HO-20261009-03: PR #109 currently open/draft/nonmergeable; main already has PLAN_TAGS, aliases, optional metadata and tests. Grok report confirms equivalence. Do not merge duplicate code; close only with appropriate approval.
- HO-20261010-13: claimed; HO-14 render already done. Reconcile record without duplicate render.
- HO-20261009-08: OAuth scope/channel check blocked. xAI provider separately reported HTTP 403. No blind retries, no secrets.
- Short onion human rights/speech/sync/captions review remains required before any publish.
- No GitHub combined commit statuses were returned for the repair commits; CI green is NOT established.

## Next test
Enforce validation before merge/direct write; add regression test rejecting placeholder/shell substitution; run real CI; verify GitHub read-back; then reconcile stale handoffs. No claim of green before CI and user-only authorization gates.
