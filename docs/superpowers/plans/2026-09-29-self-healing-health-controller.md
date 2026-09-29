# Self-Healing Health Controller Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add evidence-based health, safe self-healing decisions, and free-first provider routing without making external services or PayoutLens part of the repair surface.

**Architecture:** Add small focused Python modules for health state/evidence, routing, and controller decisions; keep existing workers intact and integrate only after unit contracts are green. Local JSONL remains canonical evidence and external observability stays best-effort.

**Tech Stack:** Python stdlib, pytest/unittest-compatible existing test harness, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-29-self-healing-health-controller.md`

## Global Constraints
- PayoutLens excluded from all controller targets and writes.
- No paid provider required; paid routing requires explicit opt-in.
- No blind retry for 401/403/OAuth/payment/account-consent failures.
- Existing worker behavior remains backward compatible.
- Healthy requires fresh evidence.

## Review Focus
- stale timestamps must not remain healthy
- malformed/unknown statuses fail closed
- auth/billing errors never enter repair loops
- protected PayoutLens names/paths cannot bypass exclusion by case
- external observability failures cannot fail local health recording

---

### Task 1: Health state and stale-green detection
**Files:** Create `scripts/system_health.py`; Test `tests/test_system_health.py`.
**Produces:** `HealthEvidence`, `effective_status()`, `is_protected_target()`.
- [ ] Write failing tests for fresh healthy, stale healthy -> degraded/stale_green, unknown status -> failed, case-insensitive PayoutLens protection.
- [ ] Run focused tests and confirm failure.
- [ ] Implement minimal stdlib module.
- [ ] Run focused tests and confirm pass.

### Task 2: Free-first provider router
**Files:** Create `scripts/provider_router.py`; Test `tests/test_provider_router.py`.
**Produces:** `ProviderCandidate`, `select_provider()`.
- [ ] Write failing tests for local_free > cloud_free > paid, paid opt-in, unhealthy skip, auth/billing no-retry metadata.
- [ ] Run focused tests and confirm failure.
- [ ] Implement deterministic selector.
- [ ] Run focused tests and confirm pass.

### Task 3: Safe self-healing controller
**Files:** Create `scripts/health_controller.py`; Test `tests/test_health_controller.py`.
**Consumes:** Task 1 health contracts. **Produces:** `ControllerDecision`, `decide_action()`.
- [ ] Write failing tests for failed allowlisted repair, mandatory retest, external_wait no-repair, disabled_optional no-repair, destructive/unknown fail-closed, PayoutLens rejection.
- [ ] Verify RED.
- [ ] Implement decision engine with explicit repair allowlist.
- [ ] Verify GREEN.

### Task 4: Local observability and Shorts isolation
**Files:** Modify/add focused integration helpers only; Test `tests/test_health_integration.py`.
- [ ] Write failing tests proving local JSONL survives external sink exception and publish external_wait does not fail production/preflight health.
- [ ] Verify RED.
- [ ] Implement minimal integration.
- [ ] Verify GREEN.

### Task 5: Whole-system verification
- [ ] Run all unit/integration tests.
- [ ] Run compile check.
- [ ] Run secret-pattern guard.
- [ ] Confirm protected PayoutLens paths unchanged.
- [ ] Open PR; inspect GitHub Actions. Do not merge unless CI is green and merge is explicitly authorized.