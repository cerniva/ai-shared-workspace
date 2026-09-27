# API-First Automation Design

## Goal
Extend the existing ai-shared-workspace into a reliable automation control plane for research, Shorts and Shopify without replacing working bridges or browser workers.

## Architecture
ChatGPT acts as the orchestrator. Work is routed API-first: dedicated provider/API adapters are preferred, while the existing browser_worker and TinyFish are fallbacks only when an API cannot perform the required operation.

Four logical workers are used:
1. research-worker — search, extraction, evidence and reusable research records.
2. shorts-worker — topic selection, production handoff, YouTube publishing/analytics integration.
3. shopify-worker — product research, catalog preparation and Shopify Admin API integration.
4. browser-worker — existing browser automation for unsupported UI-only operations.

## Research routing
Search providers (Exa/Tavily when configured) discover sources. Extraction uses one primary extractor with fallbacks rather than calling Crawl4AI, Firecrawl and Jina redundantly. Research outputs record source, timestamp, query, evidence and downstream purpose.

## API-first policy
YouTube Data/Analytics APIs and Shopify Admin API are preferred over UI automation. Browser automation is used only for missing API capabilities or explicit UI verification. CAPTCHA, MFA and account-security challenges are never bypassed.

## Safety gates
Read-only research, parsing, tests and analytics can run without a human gate. Spending money, changing credentials/secrets, payment settings, destructive actions and irreversible publishing/account actions require an explicit safety gate unless an existing narrowly scoped workflow already has the required authorization.

## Existing system compatibility
Keep current Grok, Gemini, Meta, TinyFish, Firecrawl fallback, YouTube upload, DESK/PROTOCOL and worker orchestration components. New routing must wrap/reuse them rather than duplicate them.

## State and observability
Every job has a job id, worker, provider selected, fallback reason, status and timestamp. Failures must be explicit; no fake success or fabricated provider responses. Provider degradation follows the repository's existing degradation policy.

## Rollout
Phase 1: orchestrator/router + research worker.
Phase 2: Shorts worker/API integration.
Phase 3: Shopify worker/API integration.
Phase 4: analytics feedback and browser fallback hardening.

## Success criteria
- Existing bridges continue to work.
- Research can route to an available provider and degrade cleanly.
- API-capable operations do not default to browser automation.
- Missing credentials fail closed with a useful status.
- Tests cover routing, fallback and safety-gate behavior.
