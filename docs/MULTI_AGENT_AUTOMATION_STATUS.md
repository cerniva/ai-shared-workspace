# AI automation system — verified status and remaining blockers

Audit date: 2026-09-29  
Repository: cerniva/ai-shared-workspace  
Owner: CORE-05

## Verified now

- GitHub remains the shared coordination and audit hub: state, task queue, agent message channels and bounded GitHub Actions jobs are the source of truth.
- The API-first foundation is on `main`: `orchestrator/`, `research_worker/`, `shorts_worker/` and `shopify_worker/`, with integration tests for API preference, graceful degradation and irreversible-action gates.
- `worker-orchestration-tests` watches, compiles and secret-scans the API-first worker modules plus `browser_worker/`. The expanded CI run `36350288238` passed.
- Browser planning `auto` order is implemented as Gemini → OpenAI → Grok → Anthropic. Explicit provider selection remains deterministic rather than silently switching providers.
- A verified Browser Worker smoke run showed the provider fallback behavior: OpenAI returned HTTP 429 `credit_balance_exhausted`, Grok returned HTTP 403 due credits/spending limit, and Gemini successfully generated the browser task. The current routing now tries the verified healthy Gemini route first, so known degraded providers do not add avoidable delay.
- Anthropic authentication is fixed: the current `ANTHROPIC_API_KEY` returned HTTP 200 from `/v1/models`. Claude message generation is paused only because the Anthropic credit balance is too low. Claude is optional and non-blocking.
- Meta Model API remains paused on the last verified HTTP 402 billing response and must not block unrelated work.
- The Browser Worker supports Playwright and guarded Skyvern execution. A Skyvern planner/worker schema mismatch found by smoke run `36349823688` was fixed in PR #25 by adapting deterministic read-only planner steps to Skyvern input and rejecting unsupported interactive steps fail-closed. Worker orchestration run `36350519493` passed after the fix.
- TinyFish is the primary web worker in source-of-truth state; Firecrawl is the web fallback.
- The zero-credit Shorts path is on `main`: local FFmpeg rendering can synthesize narration with eSpeak NG, rejects overlong narration before render, runs technical preflight, and can upload the MP4/report as a GitHub Actions artifact. This path does not itself publish to YouTube.
- CORE-05 is connected to the shared machine-readable source catalog and learning ledger through its adapter; canonical source dedup and source-linked learning read/write/read-back are covered by tests.
- Claude diagnostic workflow is manual-only. Temporary Claude retry trigger files were removed after authentication was verified.
- Stale PRs #16, #17, #20 and #24 were closed without merge after verification that they were obsolete, already resolved on `main`, or conflicted with the current explicit-provider contract. Issue #1 (initial test conversation) and Issue #2 (complex collaboration test) are closed as completed.
- The Shopify storefront password is no longer a technical blocker. The store remains private/opening-soon by plan while payment readiness is still unproven.

## Current routing

1. Shared state and task coordination: GitHub repo state/desk/queue.
2. Automated model work: Gemini is the currently verified healthy cloud planner route while OpenAI, Grok and Claude have provider-side credit/quota gates.
3. Browser planner `auto`: Gemini → OpenAI → Grok → Anthropic. Failed providers fall through; if every cloud planner fails, the Browser Worker uses the local fallback planner.
4. Browser execution: Playwright by default; guarded Skyvern is available when selected and configured.
5. Web/research route: TinyFish primary, Firecrawl fallback.
6. Provider billing/quota failures are isolated and must not stop unrelated workers.

## Remaining external gates

- **YouTube publishing:** zero-credit rendering is available, but the last verified upload blocker is OAuth `invalid_grant`; a fresh refresh token from the same OAuth client with the required YouTube upload scope is needed before automated upload can work again. Repository code alone cannot renew that user authorization.
- **Shopify launch:** payment readiness remains unproven. Do not claim the store is publicly launch-ready until payment approval/configuration is verified.
- **OpenAI API:** latest verified planner state is HTTP 429 `credit_balance_exhausted`.
- **xAI API:** latest verified state is HTTP 403 due credits/spending limit. Normal Grok chat/file-desk is a separate collaboration channel and should not be treated as down.
- **Meta Model API:** latest verified state is HTTP 402 billing.
- **Anthropic messages:** API key is valid, but message generation requires provider credit. Claude is optional and must not block Gemini/local fallback work.
- **Long-running authenticated browser sessions:** GitHub Actions remains a finite-job runtime, not a persistent logged-in 24/7 browser service. Do not claim otherwise.

## Operating rule

Continue useful work through healthy routes without waiting on a failed provider. Never fabricate a provider response, never expose secrets, and keep payments, account-security changes, destructive actions and irreversible publishing behind the existing safety gates.


## Red/yellow cleanup note

- Current main CI is green for worker orchestration, Shorts rendering, web worker, Gemini senses, desk-notify and CodeQL.
- Provider credit/billing/auth failures are external gates, not software defects; routing avoids making them block unrelated work.
- The OIDC feeder was reviewed against the official GitHub reference. No current workflow requires OIDC, so no trust-policy or permission change is being made speculatively.
