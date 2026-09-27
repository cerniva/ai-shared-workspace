# Private Replit Runtime Design

Date: 2026-09-27
Repository: `cerniva/ai-shared-workspace`
Status: approved design, implementation not started

## Purpose

Keep `cerniva/ai-shared-workspace` as the single public coordination hub while adding a private Replit runtime that can execute integrations without exposing API keys, OAuth tokens, authenticated session material, customer/store data, or other private payloads in the public repository.

The private runtime is not a second source of truth. It is an execution layer that reads bounded work from the public coordination model, performs allowed actions with private credentials, and writes only safe status/result summaries back to the public hub.

## Existing system constraints

- `PROTOCOL.md` and `state/now.json` remain the authoritative public coordination source.
- `tasks/active.json` remains the authoritative task catalogue; the runtime dispatch file only references task IDs from it.
- Existing agent handoff files, task state, and GitHub Actions workflows remain in place.
- Public repository files must never contain API keys, OAuth tokens, authenticated cookies/session data, customer/order details, or private Shopify/YouTube payloads.
- Existing bounded GitHub Actions workers remain useful for finite jobs and retries; they are not replaced by the private runtime.
- Long-running authenticated browser work and private commerce/account integrations require a private runtime and secret store.

## Goals for v1

1. Connect a private Replit runtime to the existing GitHub coordination hub.
2. Read a narrowly defined dispatch queue without changing the repo's source-of-truth model.
3. Execute only explicitly allowlisted low-risk actions.
4. Keep all credentials in Replit Secrets or an equivalent private environment store.
5. Write back safe summaries, status, timestamps, and error codes without leaking sensitive payloads.
6. Expose basic health and structured logs so failures can be diagnosed without opening the runtime interactively.
7. Make retries idempotent so the same task is not accidentally executed twice.

## Non-goals for v1

- No unattended purchases, payments, publishing, deletion, account-security changes, or credential changes.
- No general-purpose logged-in browser automation.
- No Shopify write operations.
- No YouTube upload/publish operations.
- No 24/7 promise until a persistent deployment and cost/budget policy are explicitly configured.
- No replacement of the GitHub coordination protocol.
- No second authoritative task database.
- No GitHub webhook in v1; polling is deliberately simpler and easier to audit.

## Architecture

### Public coordination layer

`cerniva/ai-shared-workspace` remains public and stores:

- task identifiers and non-sensitive task metadata,
- agent handoffs,
- execution status,
- safe result summaries,
- policy/configuration that is safe to publish.

### Private execution layer

A private Replit app/runtime hosts:

- GitHub client for the approved repository,
- task poll/dispatch logic,
- allowlist policy enforcement,
- connector adapters for approved services,
- secret access through Replit Secrets,
- structured audit logging,
- health endpoint,
- idempotency/retry handling.

No secret value is copied into GitHub, logs, prompts, or result summaries.

### v1 transport and files

v1 uses polling, not webhooks.

- `tasks/active.json`: authoritative task catalogue. Existing semantics remain unchanged.
- `tasks/runtime-dispatch.json`: non-sensitive execution queue. Every entry must reference an existing task ID in `tasks/active.json`; this file is not authoritative task state.
- `state/runtime-status.json`: sanitized execution ledger used for idempotency and operator visibility.

While the Replit runtime is active, it polls `tasks/runtime-dispatch.json` every 60 seconds. A manual worker cycle may also be triggered for testing. Sleeping or undeployed Replit instances therefore do not imply 24/7 execution.

The worker writes `state/runtime-status.json` using the latest GitHub blob/content SHA and rejects or retries on a write conflict instead of overwriting concurrent changes.

### Communication model

Primary flow:

`ChatGPT / human -> tasks/active.json + tasks/runtime-dispatch.json -> private Replit worker -> approved API/service -> state/runtime-status.json -> ChatGPT / human`

The runtime validates repository, referenced task ID, task type, connector, and action policy before execution.

## Dispatch contract

Each `tasks/runtime-dispatch.json` item contains only non-sensitive fields:

- `dispatch_id`: stable unique dispatch identifier,
- `task_id`: existing ID from `tasks/active.json`,
- `generation`: integer beginning at 1 and incremented only for an explicit re-execution,
- `task_type`: value from an allowlist,
- `connector`: target connector name,
- `operation`: requested operation name,
- `parameters`: non-sensitive parameters or public references only,
- `created_at`: timestamp,
- `status`: `queued`, `cancelled`, or `done`.

The idempotency key is `dispatch_id:generation`.

Sensitive parameters are resolved inside the private runtime from its own secret/config store or from an authenticated private connector. They must not be embedded in public task files.

## Result contract

`state/runtime-status.json` stores sanitized records containing:

- idempotency key,
- dispatch id,
- task id,
- generation,
- status: `queued`, `running`, `succeeded`, `failed`, or `blocked`,
- started/finished timestamps,
- safe human-readable summary,
- machine-readable error code,
- `retryable`: true/false,
- attempt count,
- optional public artifact/reference URL containing no secret material.

The worker must not write raw request/response bodies from private services unless they are explicitly sanitized.

A `succeeded`, `blocked`, or non-retryable `failed` record is terminal for that idempotency key. Re-execution requires an explicit generation increment in the dispatch file.

## Security model

### Secrets

- All API keys, OAuth tokens, private app credentials, and authenticated session material live only in Replit Secrets or another private secret store.
- Secret values are never committed to Git.
- Secret values are never echoed in logs.
- Secret names may be documented; values may not.

### Least privilege

Each connector receives only the minimum scopes required for its approved actions. Read-only scopes are preferred until a write operation is deliberately added in a later design.

The GitHub credential used by the worker is restricted to the approved repository and only the contents/actions needed by the bridge. It is stored only in the private runtime.

### Action policy

Every executable operation is classified as one of:

- `read`: safe information retrieval,
- `prepare`: generate drafts/plans without external publication,
- `write-low-risk`: reversible low-impact mutation explicitly allowlisted,
- `blocked-high-impact`: payments, purchases, publishing, deletion, account security, credential changes, or other irreversible/high-impact actions.

v1 enables only `read` and `prepare` by default. `write-low-risk` is disabled until separately designed and reviewed.

### Validation

Before execution, the worker validates:

1. repository identity is exactly `cerniva/ai-shared-workspace`,
2. dispatch schema,
3. referenced `task_id` exists in `tasks/active.json`,
4. task type allowlist,
5. connector allowlist,
6. operation/action policy,
7. idempotency key has not reached a terminal state,
8. required secret/configuration is present without exposing its value.

Any validation failure returns `blocked` and performs no external action.

## Reliability

### Idempotency

The idempotency key is `dispatch_id:generation`. Before running an external action, the worker checks `state/runtime-status.json`. A terminal key is never executed again.

### Retries

Only failures marked retryable may be retried. v1 uses at most 3 attempts for a single idempotency key with bounded backoff. Authentication, policy, schema, missing-task, or permission failures are non-retryable until configuration changes or a new generation is explicitly issued.

### Health

The runtime exposes a minimal `/health` check that reports only:

- service status,
- GitHub connectivity boolean,
- required connector configuration presence by boolean only,
- last successful worker cycle timestamp.

No secret values or private payload details appear in health output.

### Logging

Structured logs include:

- timestamp,
- idempotency key,
- task id,
- connector name,
- operation name,
- status,
- duration,
- sanitized error code/message.

Logs must redact authorization headers, cookies, tokens, secret values, and private response payloads.

## Repository boundary

The public repo may contain interface documentation, task schemas, policy, dispatch references, and sanitized result summaries.

The private runtime code/configuration may live in a private Replit workspace and, if later mirrored to GitHub, must use a private repository. The public repo must not receive a copy of private runtime secrets, private connector payloads, or authenticated session state.

## v1 connector scope

Initial connector scope is intentionally small:

- GitHub: read `tasks/active.json` and `tasks/runtime-dispatch.json`; write sanitized `state/runtime-status.json`.
- Synthetic connector: deterministic local `prepare` operation used only to prove the bridge without calling a paid model or external production service.
- External production services: no write connector is required to prove v1.

The first end-to-end acceptance test uses the synthetic connector so it spends no model/video credits and touches no Shopify/YouTube production data.

## Rollout

### Phase 1 — bridge foundation

- private Replit runtime,
- secret store wiring,
- GitHub authentication,
- `tasks/runtime-dispatch.json` schema,
- `state/runtime-status.json` schema,
- validation and allowlist policy,
- health/logging,
- synthetic end-to-end task.

### Phase 2 — research/model connectors

Add approved read/prepare connectors one at a time, with per-connector scopes and tests.

### Phase 3 — browser/private service workers

Only after Phase 1 and Phase 2 are stable, separately design authenticated browser sessions, Shopify/YouTube private operations, persistence beyond the public sanitized ledger, queue scaling, budget controls, and long-running deployment.

## Acceptance criteria for v1

v1 is complete only when all of the following are demonstrated:

1. A synthetic dispatch references an existing task in `tasks/active.json` and contains no sensitive payload.
2. The private Replit runtime detects it within one active polling cycle or a manual test cycle.
3. The runtime validates repo, task reference, schema, allowlists, action policy, and idempotency.
4. The synthetic operation executes exactly once.
5. The runtime writes a sanitized success record to `state/runtime-status.json`.
6. Re-reading the same `dispatch_id:generation` does not duplicate execution.
7. A generation increment permits one deliberate re-execution.
8. A disallowed or malformed dispatch is blocked before any external action.
9. Missing secret/configuration is reported as a safe error without revealing a value.
10. A simulated GitHub write conflict is retried without losing another writer's changes.
11. `/health` reports only non-sensitive status.
12. Logs contain no tokens, cookies, authorization headers, or private payloads.

## Design decision

Use the split architecture:

- public GitHub repo = coordination, protocol, safe task/status data,
- private Replit runtime = secrets and execution,
- future private GitHub repo is optional for backing up runtime source code, but is not required for v1.

Use polling for v1 rather than a webhook, and keep idempotency state in the sanitized public runtime ledger so restarts do not cause duplicate execution.

This preserves the existing GitHub workflow, avoids duplicating the source of truth, and creates a safe path for progressively adding integrations later.