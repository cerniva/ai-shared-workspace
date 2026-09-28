# Research Router & Source Library

Status: active
Updated: 2026-09-28

## Goal
Use the cheapest reliable source first, deepen only when needed, cross-check important claims, and save reusable source knowledge instead of repeating the same discovery work.

## Routing
1. Existing project knowledge -> search `state/`, `tasks/` and `knowledge/` first so recent verified work is reused before new external research.
2. Fast/current public question -> OpenAI Web Search.
3. Google/TinyFish Search -> discovery layer for new sources, trends, competitors, products, technical solutions and official pages; a search result/snippet is never sufficient evidence by itself for a critical claim.
4. Semantic/deep discovery -> Exa when available.
5. Page extraction / JS-heavy sites / crawl -> Firecrawl when available.
6. Broad ranked web retrieval / research API -> Parallel Search when available.
7. Interactive website actions -> browser worker/TinyFish; do not use scraping when clicks/login/state changes are required.
8. YouTube public research -> use official YouTube/Creator/Help material for platform rules and public videos/channels for format, hook, topic and competitor observations.
9. vidIQ -> YouTube keyword, trend, outlier, competitor and owned-channel analytics support; avoid duplicating the same discovery already answered by Google/TinyFish.
10. Metricool -> owned YouTube scheduling/publishing and supported analytics; a planned post is not `DONE` until the publish/read-back succeeds.
11. Video/Shorts production decisions -> read `knowledge/video-production-learning-pool.md` before repeating external research; filter cheaply with public YouTube metadata/transcripts/comments, then use expensive scene-by-scene analysis only on a small high-value subset.

## Verification rules
- Important factual claims: prefer primary/official sources.
- Search result snippets are discovery signals, not final evidence; open the underlying source before promoting a critical claim.
- Official YouTube/Google platform documentation and owned-channel analytics outrank creator commentary for platform behavior.
- Finance, payments, security, legal/compliance, permanent decisions: cross-check with at least 2 independent high-quality sources when practical.
- A YouTube creator video is opinion/learning evidence for finance or technical claims unless the claim is independently verified from primary/high-quality sources.
- Time-sensitive claims must carry retrieval/publication date when available.
- If sources conflict, preserve the disagreement; do not silently merge it.
- Never fabricate access, freshness, monitoring, citations, or completed actions.

## Cost / efficiency
- Do not call every provider for every query.
- Escalate only when the first source is incomplete, weak, blocked, stale, or the decision is high impact.
- Cache reusable source notes in `knowledge/` with: topic, URL/source, date checked, strengths, weaknesses, and intended use.
- Avoid duplicate searches when a recent verified result already answers the same question.
- Google/TinyFish, YouTube and vidIQ have complementary roles: discovery -> video/platform evidence -> YouTube-specific metrics. Do not run all three merely to repeat the same search.
- For public video research, prefer metadata/search -> transcript -> comments/related -> owned analytics -> targeted visual watch. Do not spend credits watching every candidate.

## Team flow
Research -> ChatGPT synthesis -> Grok second check when required by team protocol -> Gemini after a decision when additional review is useful/required -> final decision/report.

## Domain source priorities
- Code/software: official docs, repositories, release notes, issue trackers; Google/TinyFish may discover them but the official technical source is authoritative.
- Finance/markets: regulator/exchange/company filings and official data first; then reputable financial reporting/research. YouTube creator content remains opinion/learning unless independently verified; official institution/company channels are primary only for their own statements.
- Shopify/e-commerce: Shopify/payment-provider/supplier official docs first; Google/SEO tools for demand and competitor discovery; marketplace evidence and customer/community signals second.
- Shorts/content: platform documentation + Google/TinyFish discovery + YouTube/vidIQ trend/competitor evidence + authorized Metricool/YouTube analytics. Reusable production observations live in `knowledge/video-production-learning-pool.md`; external success patterns are hypotheses until our own analytics validate them.
- Cooking/food safety: government/standards bodies, universities, recognized professional references.

## Current validated capabilities
- OpenAI Responses API supports built-in web search and external/custom tools.
- TinyFish Search returned official YouTube/Google results and TinyFish Fetch read public Google and YouTube surfaces on 2026-09-28.
- vidIQ returned an authorized owned YouTube channel on 2026-09-28; paid analytics/research calls remain credit-sensitive and should be used only when decision value justifies them.
- Metricool brand settings returned a connected YouTube network on 2026-09-28; publishing still requires a ready video and explicit authorized publish action.
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
