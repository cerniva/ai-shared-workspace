# Private Replit Runtime Design

Date: 2026-09-27
Repository: `cerniva/ai-shared-workspace`
Status: approved design, implementation not started

## Purpose

Keep `cerniva/ai-shared-workspace` as the single public coordination hub while adding a private Replit runtime that can execute integrations without exposing API keys, OAuth tokens, authenticated session material, customer/store data, or other private payloads in the public repository.

The private runtime is not a second source of truth. It is an execution layer that reads bounded work from the public coordination model, performs allowed actions with private credentials, and writes only safe status/result summaries back to the public hub.

## Existing system constraints

- `PROTOCOL.md` and `state/now.json` remain the authoritative public coordination source.
- Existing agent handoff files, task state, and GitHub Actions workflows remain in place.
- Public repository files must never contain API keys, OAuth tokens, authenticated cookies/session data, customer/order details, or private Shopify/YouTube payloads.
- Existing bounded GitHub Actions workers remain useful for finite jobs and retries; they are not replaced by the private runtime.
- Long-running authenticated browser work and private commerce/account integrations require a private runtime and secret store.

## Goals for v1

1. Connect a private Replit runtime to the existing GitHub coordination hub.
2. Read a narrowly defined queue of executable tasks without changing the repo's source-of-truth model.
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
- No second task database as a competing source of truth.

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
- idempotency/retry state.

No secret value is copied into GitHub, logs, prompts, or result summaries.

### Communication model

Primary flow:

`ChatGPT / human -> GitHub coordination hub -> private Replit worker -> approved API/service -> sanitized result -> GitHub coordination hub`

The runtime should prefer pull/poll or an authenticated webhook that consumes only the minimum public task metadata needed to dispatch work. The runtime must validate repository, task type, and action policy before execution.

## Task contract

The worker accepts only tasks that contain all of the following non-sensitive fields:

- stable task id,
- task type from an allowlist,
- target connector name,
- requested operation name,
- non-sensitive parameters or references,
- created timestamp,
- optional retry count.

Sensitive parameters must be resolved inside the private runtime from its own secret/config store or from an authenticated private connector. They must not be embedded in public task files.

## Result contract

The worker may write back:

- task id,
- status: `queued`, `running`, `succeeded`, `failed`, or `blocked`,
- started/finished timestamps,
- safe human-readable summary,
- machine-readable error code,
- retryable: true/false,
- optional public artifact/reference URL that contains no secret material.

The worker must not write raw request/response bodies from private services unless they are explicitly sanitized.

## Security model

### Secrets

- All API keys, OAuth tokens, private app credentials, and authenticated session material live only in Replit Secrets or another private secret store.
- Secret values are never committed to Git.
- Secret values are never echoed in logs.
- Secret names may be documented; values may not.

### Least privilege

Each connector receives only the minimum scopes required for its approved actions. Read-only scopes are preferred until a write operation is deliberately added in a later design.

### Action policy

Every executable operation is classified as one of:

- `read`: safe information retrieval,
- `prepare`: generate drafts/plans without external publication,
- `write-low-risk`: reversible low-impact mutation explicitly allowlisted,
- `blocked-high-impact`: payments, purchases, publishing, deletion, account security, credential changes, or other irreversible/high-impact actions.

v1 enables only `read` and `prepare` by default. `write-low-risk` is disabled until separately designed and reviewed.

### Validation

Before execution, the worker validates:

1. repository identity,
2. task schema,
3. task type allowlist,
4. connector allowlist,
5. action policy,
6. idempotency key,
7. secret availability without exposing the value.

Any validation failure returns `blocked` and performs no external action.

## Reliability

### Idempotency

Each task uses its stable task id as the base idempotency key. A completed task is not executed again unless a new explicit retry generation/version is created.

### Retries

Only failures marked retryable may be retried. Retries use bounded backoff and a maximum attempt count. Authentication, policy, schema, or permission failures are non-retryable until configuration changes.

### Health

The runtime exposes a minimal health check that reports only:

- service up/down,
- GitHub connectivity status,
- connector configuration presence by boolean only,
- last successful worker cycle timestamp.

No secret values or private payload details appear in health output.

### Logging

Structured logs include:

- timestamp,
- task id,
- connector name,
- operation name,
- status,
- duration,
- sanitized error code/message.

Logs must redact authorization headers, cookies, tokens, secret values, and private response payloads.

## Repository boundary

The public repo may contain interface documentation, task schemas, policy, and sanitized result summaries.

The private runtime code/configuration may live in a private Replit workspace and, if later mirrored to GitHub, must use a private repository. The public repo must not receive a copy of private runtime secrets, private connector payloads, or authenticated session state.

## v1 connector scope

Initial connector scope is intentionally small:

- GitHub: read approved coordination files and write sanitized status/result summaries.
- External services: no production write connector is required to prove v1.

The first end-to-end acceptance test uses a harmless synthetic task that proves queue intake, policy validation, execution, sanitized result write-back, retry protection, and health reporting without spending model/video credits or touching Shopify/YouTube production data.

## Rollout

### Phase 1 — bridge foundation

- private Replit runtime,
- secret store wiring,
- GitHub authentication,
- task schema validation,
- allowlist policy,
- health/logging,
- synthetic end-to-end task.

### Phase 2 — research/model connectors

Add approved read/prepare connectors one at a time, with per-connector scopes and tests.

### Phase 3 — browser/private service workers

Only after Phase 1 and Phase 2 are stable, separately design authenticated browser sessions, Shopify/YouTube private operations, persistence, queue storage, budget controls, and long-running deployment.

## Acceptance criteria for v1

v1 is complete only when all of the following are demonstrated:

1. A synthetic task appears in the public coordination hub with no sensitive payload.
2. The private Replit runtime detects and validates it.
3. The runtime executes exactly once.
4. The runtime writes back a sanitized success result.
5. Re-running the same task does not duplicate execution.
6. A disallowed task is blocked before any external action.
7. Missing secret/configuration is reported as a safe error without revealing a value.
8. Health reporting works without exposing sensitive information.
9. Logs contain no tokens, cookies, authorization headers, or private payloads.

## Design decision

Use the split architecture:

- public GitHub repo = coordination, protocol, safe task/status data,
- private Replit runtime = secrets and execution,
- future private GitHub repo is optional for backing up runtime source code, but is not required for v1.

This preserves the existing GitHub workflow, avoids duplicating the source of truth, and creates a safe path for progressively adding integrations later.