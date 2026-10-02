# 2026-10-02 knowledge bridge gap

- Timestamp: 2026-10-02T10:08:00+03:00
- Status: CONTINUE
- Decision: CONSENSUS on Shorts video-only/content-probe DONE. New delta is the knowledge-library source bridge gap.
- ChatGPT view: Shorts reconciliation is DONE; next safe work is the highest real open issue, else Bilgi Kütüphanesi without deleting existing knowledge. Issue #101 stays BLOCKED_EXTERNAL.
- Grok analysis: Independent read agrees. Open issue is only #101. Open PR #99 is a stale-base docs PR (base 3827a429, head 64af49a) and was not merged. No PayoutLens change.

## GitHub evidence
- main HEAD at read: 4be0b1f8ff577a85f68f4cf40e19a4132f91df8d
- PR #103: closed, merged true, merge commit f11566bfb1ec7c61630400a3ae1090d516ffebf5
- PR #96/#97 not reopened; not treated as active.
- Catalog before: knowledge/source_catalog.json blob 8707ef82674d4937644c2eaa92e3bd5ce62475ce, 20 sources, updated_at 2026-09-29T00:04:00+00:00
- Ledger before: knowledge/learning_ledger.json blob 6f070a61fc76a319c6dc44a649c174cf4ad330f1, 3 learnings, updated_at 2026-09-28T03:02:50+00:00
- Human notes already on main and left unchanged:
  - knowledge/2026-10-02-youtube-shorts-originality-music-monetization.md
  - knowledge/2026-10-02-youtube-shorts-clickable-link-routing.md
  - knowledge/2026-10-02-youtube-shorts-metric-change.md
  - knowledge/2026-10-02-youtube-shorts-metric-timeline-correction.md
  - knowledge/2026-10-02-youtube-shorts-ab-test-limit.md

## Problem
Markdown knowledge from 2026-10-02 cited official YouTube URLs that were absent from the machine source catalog. learning_bridge fail-closes on unknown source_id, so those notes were not usable as machine-bridge evidence.

## Root cause
Human-readable notes were committed without a knowledge_bridge.py add / learning_bridge.py add pass. knowledge/RESEARCH_ROUTER.md says a Markdown entry alone is not proof the machine bridge was used.

## Prior attempts
No prior successful catalog promotion of these five notes. Existing src_d9ad3569da502ff8 still points at the hl=en form of answer/1311392. Canonical add of the queryless URL created a second stable id src_7b59e187607e2f7a. Existing record was not deleted.

## Change
Append-only bridge writes:
- source catalog 20 -> 29, validate source_count 29
- learning ledger 3 -> 7, validate learning_count 7
- new learning ids: learn_7ffa70a4b15fd05a, learn_293aa61e66bcffee, learn_a039e3768b1d2d0d, learn_0611155a6c2f111c
- gmail dedup ledger append for this verified thread message only

## Tests
- python3 scripts/knowledge_bridge.py validate -> valid true, source_count 29
- python3 scripts/learning_bridge.py validate -> valid true, learning_count 7
- CI not yet recorded in this file; workflow read-back belongs after the PR push.

## Risks / rollback
- Risk: duplicate 1311392 canonical forms. Mitigation: both ids remain; no overwrite.
- Rollback: revert this branch commit. Markdown notes stay.

## Not done
- PR #99 not merged.
- Issue #101 not retried.
- PayoutLens untouched.
