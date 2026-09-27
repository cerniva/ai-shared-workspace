# API-First Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an API-first orchestrator and research foundation, then connect Shorts and Shopify workers with safe browser fallbacks.

**Architecture:** A Python orchestrator routes typed jobs to focused workers. Provider adapters expose availability and execution results; API adapters are preferred and browser_worker/TinyFish are explicit fallbacks. Existing bridges and policies remain authoritative.

**Tech Stack:** Python, pytest, GitHub Actions, existing browser_worker/TinyFish/Firecrawl components, provider HTTP APIs.

**Spec:** `docs/superpowers/specs/2026-09-27-api-first-automation-design.md`

## Global Constraints
- Do not replace existing Grok/Gemini/Meta/TinyFish bridges.
- Fail closed when credentials are absent.
- Never fabricate successful provider responses.
- API-first; browser automation is fallback.
- CAPTCHA/MFA/security challenges are not bypassed.
- Spending, secrets, payment settings, destructive actions and irreversible publishing require a safety gate.

## Review Focus
- Missing provider credentials produce a blocked/degraded result, not fake success.
- Provider timeout/error falls back only to an allowed provider.
- Safety-gated jobs cannot execute accidentally.
- Existing browser_worker policy remains enforced.
- Existing workflows remain compatible.

---

### Task 1: Orchestrator routing core

**Files:**
- Create: `orchestrator/__init__.py`
- Create: `orchestrator/models.py`
- Create: `orchestrator/router.py`
- Test: `tests/test_orchestrator_router.py`

**Interfaces:**
- Produces: `Job`, `JobResult`, `Provider`, `route_job(job, providers)`.

- [ ] Write failing tests for API preference, allowed fallback, missing credentials and safety-gated jobs.
- [ ] Run `pytest tests/test_orchestrator_router.py -v` and verify failure.
- [ ] Implement minimal typed routing core.
- [ ] Re-run tests and verify PASS.
- [ ] Commit `feat: add API-first orchestration core`.

### Task 2: Research worker

**Files:**
- Create: `research_worker/__init__.py`
- Create: `research_worker/worker.py`
- Create: `research_worker/providers.py`
- Test: `tests/test_research_worker.py`

**Interfaces:**
- Consumes: orchestrator provider/result models.
- Produces: `research(query, purpose) -> JobResult` with evidence metadata.

- [ ] Write failing tests for source metadata, primary extraction and fallback behavior.
- [ ] Run tests and verify failure.
- [ ] Implement provider adapters that fail closed when keys are missing and reuse Firecrawl fallback where appropriate.
- [ ] Run tests and verify PASS.
- [ ] Commit `feat: add research worker routing`.

### Task 3: Shorts worker routing

**Files:**
- Create: `shorts_worker/__init__.py`
- Create: `shorts_worker/worker.py`
- Test: `tests/test_shorts_worker.py`

**Interfaces:**
- Consumes: research results and YouTube API adapter.
- Produces: draft/publish/analytics job results; publishing remains safety-gated according to spec.

- [ ] Write failing tests for research-to-draft flow, API preference and publish gate.
- [ ] Implement minimal Shorts routing while reusing the existing YouTube upload workflow contract.
- [ ] Run tests and verify PASS.
- [ ] Commit `feat: add Shorts worker routing`.

### Task 4: Shopify worker routing

**Files:**
- Create: `shopify_worker/__init__.py`
- Create: `shopify_worker/worker.py`
- Test: `tests/test_shopify_worker.py`

**Interfaces:**
- Consumes: research results and Shopify Admin API adapter.
- Produces: product draft/catalog job results; browser fallback only for unsupported UI-only operations.

- [ ] Write failing tests for API preference, missing credentials, browser fallback and irreversible-action gate.
- [ ] Implement minimal Shopify routing.
- [ ] Run tests and verify PASS.
- [ ] Commit `feat: add Shopify worker routing`.

### Task 5: Integration and CI

**Files:**
- Modify: `.github/workflows/worker-orchestration-tests.yml`
- Create/Modify: integration tests under `tests/`.
- Modify: `docs/MULTI_AGENT_AUTOMATION_STATUS.md` only after verified results.

**Interfaces:**
- Consumes all worker contracts.
- Produces a CI-verified routing layer.

- [ ] Add integration tests proving API-first selection, degradation and safety gates.
- [ ] Run full relevant pytest suite.
- [ ] Update CI to execute new tests.
- [ ] Record only verified status in documentation.
- [ ] Commit `test: verify API-first automation routing`.
