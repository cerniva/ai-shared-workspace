# AI Worker Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a tested, secret-safe shared queue and provider-worker runner so Grok/Gemini results can enter the common workspace for ChatGPT review without duplicate execution or fabricated activity.

**Architecture:** A small queue module owns state transitions and idempotency; provider adapters share one interface; a runner claims jobs and writes structured results; ChatGPT review is a separate gate. GitHub persists durable state while a real scheduler/host invokes the runner.

**Tech Stack:** Existing repository runtime, JSON durable state, GitHub, provider HTTP APIs behind adapters, existing test framework.

**Spec:** `docs/superpowers/specs/2026-09-26-ai-worker-orchestration-design.md`

## Global Constraints
- No secrets committed to GitHub.
- No autonomous purchases or subscription upgrades.
- Workers cannot self-review or self-apply results.
- Retries are bounded and duplicate execution must be idempotent.
- Missing provider credentials must produce a truthful blocked state.

## Review Focus
- Duplicate invocation must not duplicate a result.
- Expired claim must become retryable without concurrent ownership.
- Missing/empty credential must never trigger a provider request.
- Invalid state transition must be rejected.
- Exhausted attempts must end in dead-letter.

---

### Task 1: Queue contract and transition validator
**Files:** Create focused queue/state module and tests following the repository's existing runtime layout; add a durable queue JSON file under `state/`.
**Interfaces:** Produces `claim(jobId, worker)`, `complete(jobId, result)`, `fail(jobId, reason, retryable)`, and transition validation.
- [ ] Write failing tests for legal transitions, illegal transitions, duplicate completion and claim lease expiry.
- [ ] Run tests and confirm failure.
- [ ] Implement minimal queue/state logic and schema.
- [ ] Run tests and confirm pass.
- [ ] Commit.

### Task 2: Common provider adapter and mock workers
**Files:** Create provider interface, Grok/Gemini adapter shells, deterministic mock adapter and tests.
**Interfaces:** Consumes claimed work item; produces structured evidence/result contract from the spec.
- [ ] Write failing tests for normalized result shape and missing-secret blocked behavior.
- [ ] Run tests and confirm failure.
- [ ] Implement interface, mocks and secret guards; no live provider call is required for tests.
- [ ] Run tests and confirm pass.
- [ ] Commit.

### Task 3: Runner, retries and dead-letter
**Files:** Create runner plus tests and dead-letter durable state.
**Interfaces:** Consumes queue + provider adapter; produces completed/retryable_failed/blocked/dead_letter state.
- [ ] Write failing tests for one successful mock run, retry, max-attempt exhaustion and provider isolation.
- [ ] Run tests and confirm failure.
- [ ] Implement minimal runner and bounded retry policy.
- [ ] Run tests and confirm pass.
- [ ] Commit.

### Task 4: ChatGPT review gate and lessons promotion
**Files:** Create review module/tests and integrate with `knowledge/lessons.md` through an explicit accepted-result path.
**Interfaces:** `review(jobId, verdict, rationale, action, metric)`; only `accept`/`merge` can become applied.
- [ ] Write failing tests proving unreviewed/rejected worker output cannot become an applied lesson.
- [ ] Run tests and confirm failure.
- [ ] Implement review gate and append-only promotion metadata.
- [ ] Run tests and confirm pass.
- [ ] Commit.

### Task 5: Real provider wiring and operational docs
**Files:** Provider config/example env documentation, runner entry point, operating guide and integration tests using mocks.
**Interfaces:** Reads provider secrets from environment only; reports provider/model/timing/cost metadata when available.
- [ ] Write failing configuration tests for absent/invalid provider configuration.
- [ ] Run tests and confirm failure.
- [ ] Wire xAI/Gemini adapters without embedding credentials; add scheduler/hosting instructions.
- [ ] Run full test suite and static checks.
- [ ] Verify repository contains no secret values and mock end-to-end queue -> worker -> review flow passes.
- [ ] Commit.

## Self-review
Spec coverage: queue, provider isolation, review gate, retries/dead-letter, secrets and compatibility are represented. Interfaces use one state machine throughout. Review-focus failure modes are assigned to Tasks 1-3. Live calls remain blocked until user-supplied provider credentials exist; mocks allow the architecture to be verified without pretending Grok/Gemini ran.
