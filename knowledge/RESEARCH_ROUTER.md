# Research Router & Source Library

Status: active
Updated: 2026-09-27

## Goal
Use the cheapest reliable source first, deepen only when needed, cross-check important claims, and save reusable source knowledge instead of repeating the same discovery work.

## Routing
1. Fast/current public question -> OpenAI Web Search.
2. Semantic/deep discovery -> Exa when available.
3. Page extraction / JS-heavy sites / crawl -> Firecrawl when available.
4. Broad ranked web retrieval / research API -> Parallel Search when available.
5. Interactive website actions -> browser worker/TinyFish; do not use scraping when clicks/login/state changes are required.
6. Existing project knowledge -> search `knowledge/` before new external research.

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

## Team flow
Research -> ChatGPT synthesis -> Grok second check when required by team protocol -> Gemini after a decision when additional review is useful/required -> final decision/report.

## Domain source priorities
- Code/software: official docs, repositories, release notes, issue trackers.
- Finance/markets: regulator/exchange/company filings and official data first; then reputable financial reporting/research.
- Shopify/e-commerce: Shopify/payment-provider/supplier official docs first; marketplace evidence and customer/community signals second.
- Shorts/content: platform documentation + current platform/search evidence + channel/video performance data when authorized.
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
