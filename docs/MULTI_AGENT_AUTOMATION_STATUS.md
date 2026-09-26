# AI automation system — verified status and remaining blockers

Audit date: 2026-09-26  
Repository: cerniva/ai-shared-workspace  
Owner: CORE-05

## Verified now

- The repo already has one shared file desk, append-only agent channels, a task queue, and a source-of-truth state file. Keep this as the only coordination hub; do not add api.senkron.bot or a second protocol.
- Gemini has a GitHub Actions worker. Its previous recorded run hit the free-tier quota limit (20 requests/day for the selected model). Furkan explicitly authorized Gemini for this one planning request; its new reply is not present yet.
- Grok currently contributes through the repo handoff channel. The repo README says there is no always-running Grok worker.
- A Meta Model API worker exists in scripts/meta_senses.py and .github/workflows/meta-senses.yml. It calls Muse Spark and writes to messages/from-meta.md; the last recorded worker output says META_MODEL_API_KEY is missing. This is a model API route, not the Meta AI share page or a browser session.
- The Meta AI share page is analysis input only. It does not itself deploy a server, establish API credentials, or connect Shopify.
- GitHub Actions Browser Worker can run a finite browser job. PR #10 added a hostname allowlist, read-only default, restricted interactive mode, sensitive-field and high-impact control blocks, and limited model keys to the planning step. It does not keep a logged-in browser session or run 24/7.
- The lower-level scripts/browser_executor.py is only an HTTP GET canary. It does not click or log in.
- The public repo's status explicitly blocks private Shopify connector payloads. Do not put private store data or credentials in public files.
- No Railway project currently exists in the connected Railway workspace. A 24/7 service therefore has not been deployed.

## Smallest practical path

1. Keep GitHub as the shared task/status record.
2. Use GitHub Actions for bounded jobs and retries; keep model keys in Actions Secrets.
3. Use the Meta paste bridge at no API cost when a one-off Meta AI opinion is enough. To automate Muse Spark, generate a Model API key at dev.meta.ai and add it only as the META_MODEL_API_KEY Actions secret.
4. For frequent Gemini jobs, wait for quota reset or set a usage/billing limit in Google AI Studio. Do not enable paid usage without a spending limit.
5. Before Shopify writes or logged-in browsing, move those workers and credentials to a private runtime/repository. Grant a Shopify app only the scopes the worker needs. Keep publish, payment, deletion, account-security and other high-impact actions out of unattended execution.
6. Treat a 24/7 browser worker as a separate deployment: private host, authenticated queue endpoint, persistent database/queue, secret store, health checks, audit log, domain/action policy and explicit budget. The connected Railway account currently has zero projects, so this would create new infrastructure and may incur charges.

## Open items

- CORE-05 multi-agent review: requests sent; independent Grok/Gemini/Meta responses have not all arrived.
- Meta automatic worker: waiting on META_MODEL_API_KEY and a successful smoke test.
- Gemini one-time review: queued; previous quota error must clear before a successful response.
- Long-running authenticated browser actions: not yet deployable from the current public workspace. Code can be tested in Actions, but no private persistent runtime or authenticated session store is configured.
