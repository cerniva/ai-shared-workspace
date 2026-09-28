# Research Router & Source Library

Status: active
Updated: 2026-09-28

## Goal
Use the cheapest reliable source first, deepen only when needed, cross-check important claims, and save reusable source knowledge instead of repeating the same discovery work.

## Routing
1. Fast/current public question -> OpenAI Web Search.
2. Semantic/deep discovery -> Exa when available.
3. Page extraction / JS-heavy sites / crawl -> Firecrawl when available.
4. Broad ranked web retrieval / research API -> Parallel Search when available.
5. Interactive website actions -> browser worker/TinyFish; do not use scraping when clicks/login/state changes are required.
6. Existing project knowledge -> search `knowledge/` before new external research.
7. Video/Shorts production decisions -> read `knowledge/video-production-learning-pool.md` before repeating external research; filter cheaply with public YouTube metadata/transcripts/comments, then use expensive scene-by-scene analysis only on a small high-value subset.

## Verification rules
- Important factual claims: prefer primary/official sources.
- Finance, payments, security, legal/compliance, permanent decisions: cross-check with at least 2 independent high-quality sources when practical.
- Time-sensitive claims must carry retrieval/publication date when available.
- If sources conflict, preserve the disagreement; do not silently merge it.
- Never fabricate access, freshness, monitoring, citations, or completed actions.

## Cost / efficiency
- Do not call every provider for every query.
- Escalate only when the first source is incomplete, weak, blocked, stale, or the decision is high impact.
- Cache reusable source notes in `knowledge/` with: topic, URL/source, date checked, strengths, weaknesses, and intended use.
- Avoid duplicate searches when a recent verified result already answers the same question.
- For public video research, prefer metadata/search -> transcript -> comments/related -> owned analytics -> targeted visual watch. Do not spend credits watching every candidate.

## Team flow
Research -> ChatGPT synthesis -> Grok second check when required by team protocol -> Gemini after a decision when additional review is useful/required -> final decision/report.

## Domain source priorities
- Code/software: official docs, repositories, release notes, issue trackers.
- Finance/markets: regulator/exchange/company filings and official data first; then reputable financial reporting/research.
- Shopify/e-commerce: Shopify/payment-provider/supplier official docs first; marketplace evidence and customer/community signals second.
- Shorts/content: platform documentation + current platform/search evidence + channel/video performance data when authorized. Reusable production observations live in `knowledge/video-production-learning-pool.md`; external success patterns are hypotheses until our own analytics validate them.
- Cooking/food safety: government/standards bodies, universities, recognized professional references.

## Current validated capabilities
- OpenAI Responses API supports built-in web search and external/custom tools.
- Firecrawl supports search, scrape, map and crawl workflows.
- Parallel exposes Search, Task and Chat APIs plus Remote MCP.

Provider availability and credentials must be checked at execution time; this document does not imply that every provider is authenticated.

## Machine-readable shared catalog

- `knowledge/source_catalog.json` is the central, schema-versioned source catalog. The existing Markdown files remain the human-readable, backward-compatible layer.
- Use `python3 scripts/knowledge_bridge.py find <canonical-url-or-source-id>` before adding a source, then `add` only when it provides new decision value.
- Stable IDs are derived from canonical URLs/tools. Tracking parameters are removed; duplicates are idempotent.
- Catalog writes use a POSIX file lock, atomic replace, and immediate read-back verification. This protects concurrent processes in one checkout; independent Git branches still require normal merge-conflict checks.
- Records distinguish `verified`, `user_reported`, and `unverified`; failures remain in `failure_note` instead of being silently erased.
- Secrets, credentials, sensitive URL query parameters, and personal email addresses are rejected. Do not store PII in source metadata.
- Validate with `python3 scripts/knowledge_bridge.py validate`. Other plans are not considered connected until they call this bridge and pass their own read -> write -> read-back test.

## Machine-readable learning ledger

- Reusable decisions and failures go to `knowledge/learning_ledger.json` through `scripts/learning_bridge.py`.
- Every learning must reference at least one existing `source_id`; unknown sources fail closed.
- Stable `learning_id` values deduplicate the normalized domain + claim. `supersedes` preserves history instead of silently rewriting it.
- Store decision, outcome, next measurement, failure history, fallback history, evidence status, and provenance. Secret/PII rejection and atomic read-back rules are shared with the source catalog.
- `knowledge/knowledge_index.json` is the routing index. Legacy Markdown remains readable, but a Markdown entry alone is not proof that a plan used the machine bridge.
- Remote GitHub writers must read the current blob SHA and serialize Contents API updates. On HTTP 409/422, re-read state before one bounded retry; never overwrite a concurrent delta blindly.
- Validate both layers with `python3 scripts/knowledge_bridge.py validate` and `python3 scripts/learning_bridge.py validate`.

## Shared production pool

- `knowledge/video-production-learning-pool.md` is the reusable production observation layer for Shorts/video work.
- Video/Shopify is the primary producer/consumer; Bilgi Kütüphanesi deduplicates/promotes durable entries; Sistem Geliştirmeleri uses it for production tooling/QC; Finans may consume it only when creating finance media and must never treat popularity as market evidence.
- Public video patterns are observations/hypotheses, not causal rules. Validate them against owned-channel analytics before promoting them to stable strategy.
- Do not copy scripts, footage or distinctive creative expression from analyzed public videos.

## Cross-chat synchronization

- Before meaningful work, read both `state/now.json` and `state/cross_chat_sync.json`. Treat them as the shared coordination entrypoint, not the current chat transcript alone.
- When recent user context from another conversation is available, reconcile it against live repository/service state before acting. Persist only new deltas; never duplicate unchanged tasks or stale failures.
- A user-reported connection, API key creation, login, setting change or completed manual step remains `user_reported` until the target system is independently verified. Never store the secret/token/password/API-key value.
- Live GitHub/CI/service status overrides stale email notifications and old chat reports. If an earlier failure has a later verified success, do not keep it as an open blocker.
- If another conversation introduces a new task, decision, integration or manual completion that materially changes an active plan, update `state/cross_chat_sync.json` and the relevant task/state record before continuing dependent work.
- There is no guaranteed instant push from every separate chat into the repository. Do not claim real-time synchronization. The coordinator must perform reconciliation passes; hourly plans provide eventual synchronization when they can access recent user context.
