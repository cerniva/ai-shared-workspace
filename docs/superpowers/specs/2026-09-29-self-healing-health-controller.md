# Self-Healing Health Controller Design

## Goal
Make the existing workspace detect stale-green and real failures, classify external waits separately, prefer free/local fallbacks, and attempt only bounded safe repairs before retesting.

## Constraints
- PayoutLens is strictly excluded from discovery, repair targets, writes, and generated tasks.
- No paid API/provider becomes required. Routing order is local/free -> free cloud -> optional paid only when explicitly enabled.
- 401/403/OAuth/payment/account-consent failures are external_wait or disabled_optional; never blind-retried or auto-repaired.
- Existing worker flows remain backward compatible.
- A component is healthy only with fresh evidence; configuration presence alone is insufficient.
- Shorts research/production/rights/audio/preflight may proceed while publishing is external_wait; publish remains fail-closed.
- Local JSONL is canonical observability; Langfuse/Sentry are optional sinks.

## State Model
`healthy`, `degraded`, `external_wait`, `disabled_optional`, `failed`.

Evidence records carry component, status, checked_at, evidence kind, detail, optional remediation and freshness TTL. Expired healthy evidence becomes degraded (`stale_green`) until a smoke check refreshes it.

## Controller
A focused controller consumes health evidence and returns deterministic actions. For `failed`, it may choose an allowlisted safe repair, then requires a retest before health can return to healthy. For `external_wait` and `disabled_optional`, it records the state and does not retry. Unknown/destructive/security-sensitive repairs fail closed.

## Free-first routing
Provider candidates declare availability, cost class, and health. Selection prefers local_free, then cloud_free, then paid only when `allow_paid=true`. Auth/billing failures are not retried and the next eligible free provider is selected.

## Observability
Every controller decision is appended to local JSONL with stable event keys. External sinks are best-effort and cannot fail the controller.

## Shorts isolation
Publishing health is a separate component from production health. A publish external_wait must not mark research/render/QA/preflight failed. Rights/provenance or technical QA failure still blocks publish.

## Safety
Paths/names containing `payoutlens` (case-insensitive) are protected. The controller must reject repair/task generation for protected targets.

## Verification
Tests must cover stale-green downgrade, fresh healthy evidence, failed->safe repair->retest, no repair for external_wait, free-first routing, paid opt-in, provider auth no-retry, PayoutLens exclusion, optional observability sink failure, and publish/production isolation. Existing test suite and compile/secret guards must remain green.