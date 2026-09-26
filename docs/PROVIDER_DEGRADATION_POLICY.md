# Provider degradation policy

Date: 2026-09-26
Source of truth for live status: `state/now.json`.

## Never conflate these channels

- **Grok chat**: normal xAI/Grok conversation and red-team contribution.
- **Grok API worker**: `.github/workflows/grok-file-desk.yml` + `scripts/grok_senses.py`; requires `XAI_API_KEY`.
- **Grok Bot**: separate computer/browser agent with its own usage quota.

A Grok Bot quota failure is **not** a Grok chat outage and is **not** evidence that the xAI API is unavailable. Likewise, a missing `XAI_API_KEY` only disables the API worker.

## Current degraded routing

1. Coordination/synthesis: ChatGPT.
2. Automated model work: OpenAI worker first; Gemini as secondary where appropriate.
3. Grok red-team: normal Grok chat/file-desk handoff when available. Do not fabricate a Grok answer with another model.
4. Web/browser execution: TinyFish first, Firecrawl fallback.
5. Meta Model API: pause on HTTP 402; do not retry automatically or block unrelated work. Meta consumer chat remains a separate channel.

## Failure rules

- Provider-specific failure must not stop unrelated CORE work.
- Do not impersonate a failed provider. A fallback result must keep the actual provider identity.
- Missing credential: mark only that provider path unavailable; continue through verified alternatives.
- 401/403: permission/auth blocker; no bypass.
- 402: billing/entitlement blocker; no automatic retry storm.
- 429/5xx: transient; bounded retry/backoff only.
- Browser quota exhaustion: route public/read-only web work to the next verified browser/web worker.
- Login/MFA/payment/security changes remain human gates.

## Recovery

When a provider recovers, update `state/now.json` from fresh run evidence before restoring it to the primary route. Do not infer recovery from a subscription purchase, chat availability, or a different product under the same vendor.
