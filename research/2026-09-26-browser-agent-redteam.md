# Browser-agent architecture red-team (Grok)

Cite: MSG-20260926-browser-agent-chatgpt-001
Date: 2026-09-26
Verdict: architecture direction is correct; unrestricted browser is not v1.

## Facts
- Shopify store data already has Admin GraphQL (`scripts/connectors/shopify_client.py`).
- Policy file exists: `config/external_action_policy.json`.
- Work queue already has lease, retry, blocked, dead_letter.
- GPT-5.6 E2E job `E2E-GPT56-20260926-001` is dead_letter because of HTTP 429 (2/2 attempts). That is rate-limit, not executor failure.

## Smallest deployable v1
- Policy gate before any network.
- Allowlist default: `example.com` only.
- Executor: HTTP GET canary. No click, no login, no cookie jar.
- Shopify reads stay on GraphQL. Writes need approval.
- 429 dead-letters: `WorkQueueWithRequeue.requeue_rate_limited`.
