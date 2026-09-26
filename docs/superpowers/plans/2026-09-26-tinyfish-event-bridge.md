# TinyFish Event Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make TinyFish web work durable, idempotent, event-driven, and routable back to ChatGPT/Grok/Gemini/Meta without duplicate browser runs or polling spam.

**Architecture:** Keep `messages/inbox-tinyfish.md` and `messages/from-tinyfish.md` as the request/result source of truth. Add a small JSON run ledger plus a separate reconciliation/router script; `tinyfish_senses.py` starts or executes work and persists browser run identity, while the event bridge normalizes state transitions, deduplicates terminal events, and routes only meaningful deltas. Phase 1 is GitHub-native; no public webhook receiver or new secret is introduced.

**Tech Stack:** Python 3 stdlib (`json`, `pathlib`, `urllib`), GitHub Actions YAML, `unittest`, existing Markdown message channels.

**Spec:** `docs/superpowers/specs/2026-09-26-tinyfish-event-bridge-design.md`

## Global Constraints

- GitHub files remain the durable source of truth.
- `fetch` remains the default low-cost/read-only mode.
- Browser automation is explicit and may be metered.
- `TINYFISH_API_KEY` remains GitHub Secret only; never write secrets to repo/messages/logs.
- Preserve the existing prohibited-action gate for payment/purchase, public publish, destructive account actions, security/credential changes, secret exposure, login bypass, 2FA/MFA/CAPTCHA bypass.
- One active external browser run per task ID.
- 401/403 and 402 create one deduplicated user-action blocker; 429/5xx are retryable and must not create blocker spam or duplicate browser runs.
- Phase 1 adds no public server, webhook secret, or live metered browser requirement to tests.
- PayoutLens is untouched.

## Review Focus

- A repeated workflow invocation for an already-running `task_id` must reuse the persisted `run_id`, not create another Agent run. Covered in Task 1 tests.
- A stale/unknown browser run must retain its `run_id` and remain reconcilable rather than being treated as a fresh task. Covered in Task 2 tests.
- A terminal event replay must not append a second routed message. Covered in Task 2 tests.
- An unsupported/unknown `requested_by` value must fail locally without writing to an arbitrary channel. Covered in Task 2 tests.
- Retryable 429/5xx state must be bounded and must not add `user-action-required` entries. Covered across Tasks 1 and 2 tests.

---

### Task 1: Durable TinyFish run ledger and idempotent execution

**Files:**
- Modify: `scripts/tinyfish_senses.py`
- Create: `state/tinyfish-runs.json`
- Modify: `tests/test_tinyfish_senses.py`

**Interfaces:**
- Produces: `load_ledger(path: Path = RUNS) -> dict`, `save_ledger(ledger: dict, path: Path = RUNS) -> None`, `task_record(ledger: dict, task_id: str) -> dict | None`, `record_run_start(...) -> dict`, `record_terminal(...) -> dict`.
- Ledger keys are task IDs; each record stores at least `task_id`, `requested_by`, `mode`, `status`, `run_id`, `updated_at`, `last_error`, and `routed_event_keys`.
- Browser execution must persist a returned `run_id` before any later reconciliation step.

- [ ] **Step 1: Write failing ledger/idempotency tests**

Add tests asserting: empty/missing ledger loads as `{}`; a browser task with an existing `running` record and `run_id` does not call `run_browser`; terminal tasks do not execute again; 429/5xx updates retryable state without creating a user-action blocker; fetch behavior remains unchanged.

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `python -m unittest tests.test_tinyfish_senses -v`
Expected: FAIL because ledger/idempotency interfaces do not exist yet.

- [ ] **Step 3: Implement the minimal ledger and execution guards**

Add `RUNS = ROOT / "state" / "tinyfish-runs.json"` and the interfaces above. Keep existing parsing/safety functions intact. For browser starts, extract TinyFish's run identifier from the response (`run_id` or `id`); if absent, record a blocked/unknown response without inventing an ID. Before any external browser call, consult the ledger and skip when the same task is already `running` or terminal.

- [ ] **Step 4: Run focused tests**

Run: `python -m unittest tests.test_tinyfish_senses -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/tinyfish_senses.py tests/test_tinyfish_senses.py state/tinyfish-runs.json
git commit -m "feat: persist TinyFish run state"
```

### Task 2: Event reconciliation, dedupe, and requester routing

**Files:**
- Create: `scripts/tinyfish_event_bridge.py`
- Create: `tests/test_tinyfish_event_bridge.py`
- Read/append only at runtime: `messages/from-tinyfish.md`, `messages/chatgpt-to-grok.md`, `messages/inbox-gemini.md`, `messages/inbox-meta.md`, `messages/shared-inbox.md`, `state/tinyfish-runs.json`, `state/now.json`

**Interfaces:**
- Consumes: Task 1 ledger schema.
- Produces: `event_key(task_id: str, run_id: str, status: str) -> str`, `normalize_event(record: dict, remote: dict) -> dict`, `route_target(requested_by: str) -> Path`, `route_event(event: dict, ledger: dict) -> bool`, `reconcile_record(record: dict, api_key: str) -> dict`.
- Route mapping: `chatgpt -> messages/shared-inbox.md` with `to: chatgpt`; `grok -> messages/chatgpt-to-grok.md`; `gemini -> messages/inbox-gemini.md`; `meta -> messages/inbox-meta.md`. Unknown requesters raise/return a local validation failure and do not write a channel.
- Event key is deterministic from `task_id + run_id + terminal_status`; store it in `routed_event_keys` only after the route write succeeds.

- [ ] **Step 1: Write failing reconciliation/routing tests**

Create tests for all four route targets, unknown requester rejection, deterministic event keys, terminal replay dedupe, preservation of an unknown/stale `run_id`, and a 429/5xx remote response remaining retryable without user-action output.

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `python -m unittest tests.test_tinyfish_event_bridge -v`
Expected: FAIL because the module does not exist.

- [ ] **Step 3: Implement event normalization and routing**

Use concise Markdown event blocks containing `task_id`, `run_id`, `requested_by`, `mode`, `status`, evidence/result pointer, blocker if any, and at most one next action. Do not emit ACK-only/heartbeat messages. Keep routing writes append-only.

- [ ] **Step 4: Implement bounded reconciliation**

Only inspect ledger records in active/retryable states. Remote lookup failures must preserve the existing `run_id`; 401/403/402 classify as human-action blockers, 429/5xx as retryable. Do not create a new browser run from this module.

- [ ] **Step 5: Run focused tests**

Run: `python -m unittest tests.test_tinyfish_event_bridge -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/tinyfish_event_bridge.py tests/test_tinyfish_event_bridge.py
git commit -m "feat: route TinyFish lifecycle events"
```

### Task 3: GitHub Actions reconciliation loop and persisted state

**Files:**
- Modify: `.github/workflows/tinyfish-senses.yml`
- Create: `.github/workflows/tinyfish-event-bridge.yml`
- Modify: `tests/test_tinyfish_event_bridge.py`

**Interfaces:**
- Consumes: `scripts/tinyfish_event_bridge.py`, `state/tinyfish-runs.json`, `TINYFISH_API_KEY`.
- Produces: bounded reconciliation runs with concurrency group `tinyfish-event-bridge`, plus commits only when tracked state/message files changed.

- [ ] **Step 1: Add failing workflow-contract tests**

Add tests that read both YAML files as text and assert: TinyFish worker commits `state/tinyfish-runs.json`; event bridge has its own concurrency group; it passes `TINYFISH_API_KEY`; it invokes only the event bridge script; commit paths are limited to TinyFish state/result/routed-message/concise state files.

- [ ] **Step 2: Run the focused tests and verify failure**

Run: `python -m unittest tests.test_tinyfish_event_bridge -v`
Expected: FAIL on missing workflow/commit-state assertions.

- [ ] **Step 3: Update `tinyfish-senses.yml`**

Include `state/tinyfish-runs.json` in the result commit while preserving existing `tinyfish-senses` concurrency and bot-loop guard.

- [ ] **Step 4: Add `tinyfish-event-bridge.yml`**

Use `workflow_dispatch` plus a bounded schedule suitable for reconciliation (no faster than necessary); checkout, run `python3 scripts/tinyfish_event_bridge.py`, then commit only changed ledger/result/routed-message/`state/now.json` files. Set `contents: write`, `cancel-in-progress: false`, and a distinct concurrency group.

- [ ] **Step 5: Run focused tests**

Run: `python -m unittest tests.test_tinyfish_event_bridge -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/tinyfish-senses.yml .github/workflows/tinyfish-event-bridge.yml tests/test_tinyfish_event_bridge.py
git commit -m "ci: reconcile TinyFish events"
```

### Task 4: Protocol/schema documentation and full verification

**Files:**
- Modify: `PROTOCOL.md`
- Create: `docs/TINYFISH_EVENT_BRIDGE.md`
- Modify if required by tests only: `tests/test_tinyfish_event_bridge.py`

**Interfaces:**
- Documents the normalized task fields (`id`, `from`, `mode`, URL(s), `goal`, `status`) and event fields (`task_id`, `run_id`, `requested_by`, `mode`, `status`, evidence pointer, blocker, next action).
- Documents that all four agents may request TinyFish work, while GitHub remains source of truth and browser writes stay safety-gated.

- [ ] **Step 1: Add documentation contract assertions if useful**

Assert the protocol names `state/tinyfish-runs.json`, all four requester values, and the no-duplicate-run rule.

- [ ] **Step 2: Update protocol and add operator documentation**

Document task examples for `fetch` and `browser`, lifecycle statuses, route behavior, dedupe semantics, retry classes, cost policy, and the future webhook fast path as explicitly not yet active.

- [ ] **Step 3: Run Python compilation**

Run: `python -m py_compile scripts/tinyfish_senses.py scripts/tinyfish_event_bridge.py`
Expected: exit 0.

- [ ] **Step 4: Run TinyFish tests**

Run: `python -m unittest tests.test_tinyfish_senses tests.test_tinyfish_event_bridge -v`
Expected: all PASS; no live TinyFish browser call.

- [ ] **Step 5: Run the repository test suite**

Run: `python -m unittest discover -s tests -v`
Expected: all PASS.

- [ ] **Step 6: Verify workflow syntax without spending browser credits**

Run the repository's existing orchestration/workflow checks if present; otherwise parse/inspect workflow contracts through tests. Confirm no test calls TinyFish Agent live.

- [ ] **Step 7: Commit**

```bash
git add PROTOCOL.md docs/TINYFISH_EVENT_BRIDGE.md tests/test_tinyfish_event_bridge.py
git commit -m "docs: define TinyFish event bridge protocol"
```

### Task 5: Final evidence and non-metered smoke verification

**Files:**
- No production file required unless verification exposes a defect.

**Interfaces:**
- Consumes the completed implementation.
- Produces verification evidence only; no metered browser run is required.

- [ ] **Step 1: Re-run the complete verification commands from Task 4**

Expected: all PASS.

- [ ] **Step 2: Exercise a mocked/fixture terminal event twice**

Expected: first event routes once; second replay produces no new route entry.

- [ ] **Step 3: Exercise a normal Fetch task only if it provides new evidence**

Expected: Fetch still completes through the existing worker and records state without a browser credit charge. Skip if existing automated evidence is sufficient.

- [ ] **Step 4: Inspect `git diff` and secret hygiene**

Confirm no API key/token/credential value appears in tracked changes and PayoutLens has no changes.

- [ ] **Step 5: Record final verification commit only if evidence/docs changed**

Do not create an empty or ACK-only commit.
