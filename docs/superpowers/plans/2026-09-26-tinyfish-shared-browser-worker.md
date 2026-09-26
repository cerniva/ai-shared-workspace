# TinyFish Shared Browser Worker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the existing TinyFish fetch worker into a shared ChatGPT/Grok web execution layer with explicit fetch/browser routing, bounded browser automation, normalized results, and deduplicated user blockers.

**Architecture:** Keep the existing single GitHub queue/result channel and serialized Actions workflow. Refactor `scripts/tinyfish_senses.py` into testable parsing/routing helpers: free read-only Fetch remains the default, while only explicit `mode: browser` tasks can call TinyFish Agent `/v1/automation/run`. Browser requests are guarded before network execution and all results/blockers are normalized back into the desk files.

**Tech Stack:** Python 3 standard library (`unittest`, `urllib`, `json`, `re`, `pathlib`), GitHub Actions YAML, Markdown desk protocol.

**Spec:** `docs/superpowers/specs/2026-09-26-tinyfish-shared-browser-worker-design.md`

## Global Constraints

- Existing tasks with no `mode` remain `fetch` and must continue to work.
- `mode: browser` is the only route allowed to call TinyFish Agent.
- Browser request defaults: `browser_profile: lite`, `max_steps: 50`, `max_duration_seconds: 300`.
- No autonomous purchase/payment, external publish, deletion, account/security changes, secret submission, or login/2FA/CAPTCHA bypass.
- `TINYFISH_API_KEY` remains only in GitHub Actions secrets; never write it to repository files or outputs.
- Authenticated browser profile/vault support is out of scope for v1.
- Result content is bounded before commit.
- No live paid browser run is used for deployment verification.

## Review Focus

- Legacy `urls:` fetch task with no `mode` still routes to Fetch.
- A browser-like goal cannot accidentally invoke Agent unless `mode: browser` is explicit.
- Prohibited/high-risk goals fail locally before any Agent network call.
- Repeated missing-secret/permission/credit failures do not append duplicate open user-action records.
- TinyFish transient 429/5xx responses cannot create an unbounded retry/spend loop.

---

### Task 1: Parse and validate the shared task contract

**Files:**
- Modify: `scripts/tinyfish_senses.py`
- Create: `tests/test_tinyfish_senses.py`

**Interfaces:**
- Produces: `parse_task(block: str) -> dict[str, object]`
- Produces: `validate_task(task: dict[str, object]) -> tuple[bool, str]`
- Produces task keys: `id`, `requested_by`, `mode`, `urls`, `url`, `goal`, `status`.

- [ ] **Step 1: Write failing parser tests**

Add `unittest` cases asserting: missing `mode` becomes `fetch`; legacy `urls:` is preserved; explicit `mode: browser`, `from: grok`, `url:` and multiline `goal: |` are parsed; unsupported mode and missing browser URL/goal fail validation.

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: FAIL because shared task parsing/validation helpers do not exist.

- [ ] **Step 3: Implement parsing and validation**

Implement `parse_task(block: str) -> dict[str, object]` and `validate_task(task: dict[str, object]) -> tuple[bool, str]` in `scripts/tinyfish_senses.py`. Preserve existing allowlisted fetch URL behavior and default missing `mode` to `fetch`.

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: parser/validation tests PASS.

- [ ] **Step 5: Commit**

Commit message: `refactor: parse shared TinyFish tasks`

### Task 2: Add explicit browser request construction and safety guard

**Files:**
- Modify: `scripts/tinyfish_senses.py`
- Modify: `tests/test_tinyfish_senses.py`

**Interfaces:**
- Consumes: parsed task from Task 1.
- Produces: `browser_block_reason(task: dict[str, object]) -> str`
- Produces: `build_browser_payload(task: dict[str, object]) -> dict[str, object]`
- Produces: `run_browser(task: dict[str, object], key: str) -> dict[str, object]`

- [ ] **Step 1: Write failing browser/safety tests**

Assert browser payload uses the task URL/goal plus `browser_profile="lite"`, strict bounded agent config with 50 steps and 300 seconds; assert explicit prohibited goals involving payment/purchase, publishing, deletion, security-setting changes, secrets/passwords, or 2FA/CAPTCHA/login bypass return a local block reason; assert `fetch` tasks never call browser construction.

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: FAIL because browser helpers do not exist.

- [ ] **Step 3: Implement safety guard and Agent request**

Add `AGENT_RUN_URL = "https://agent.tinyfish.ai/v1/automation/run"`. Implement the three interfaces above using `X-API-Key`, JSON POST, one synchronous call, and no automatic retry. Guard the task before opening the request.

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: browser/safety tests PASS with network mocked.

- [ ] **Step 5: Commit**

Commit message: `feat: add guarded TinyFish browser routing`

### Task 3: Normalize outputs and deduplicate blockers

**Files:**
- Modify: `scripts/tinyfish_senses.py`
- Modify: `tests/test_tinyfish_senses.py`

**Interfaces:**
- Produces: `append_result(task: dict[str, object], status: str, data: object) -> None`
- Produces: `append_action_once(service: str, reason_code: str, reason: str) -> bool`
- Produces normalized result metadata: `task_id`, `from: tinyfish`, `requested_by`, `mode`, `status`, `created_at`.

- [ ] **Step 1: Write failing result/blocker tests**

Using temporary files/mocks, assert normalized result metadata is present, output is size-bounded, two identical open blocker attempts create only one record, and a different blocker reason may create a new record.

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: FAIL because normalized result/dedupe helpers do not exist.

- [ ] **Step 3: Implement normalized result and blocker dedupe**

Replace unconditional `append_action` behavior with stable service/reason-code dedupe against existing `status: open` records. Bound serialized result text before writing to `messages/from-tinyfish.md`.

- [ ] **Step 4: Run tests**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: result/dedupe tests PASS.

- [ ] **Step 5: Commit**

Commit message: `fix: normalize TinyFish results and dedupe blockers`

### Task 4: Route main execution and classify HTTP failures

**Files:**
- Modify: `scripts/tinyfish_senses.py`
- Modify: `tests/test_tinyfish_senses.py`

**Interfaces:**
- Consumes: parser, validator, fetch path, browser path, result writer, blocker writer.
- `main() -> int` remains the GitHub Actions entry point.

- [ ] **Step 1: Write failing routing/error tests**

Mock network and file writes. Assert legacy/default fetch routes only to Fetch; explicit browser routes only to Agent; 401/403 maps to API permission blocker; 402 maps to credit/plan blocker; 429/5xx is marked retryable/blocked without retrying; invalid task is `failed` locally; missing key creates one missing-secret blocker.

- [ ] **Step 2: Run tests and verify failure**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: FAIL on the old fetch-only `main()` behavior.

- [ ] **Step 3: Refactor `main()` routing**

Route by validated `mode`; execute at most one network call; preserve inbox status updates; classify HTTP failures without retry loops; write normalized results/diagnostics.

- [ ] **Step 4: Run full unit suite**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: all tests PASS.

- [ ] **Step 5: Commit**

Commit message: `feat: route TinyFish shared web tasks`

### Task 5: Update workflow and desk protocol

**Files:**
- Modify: `.github/workflows/tinyfish-senses.yml`
- Modify: `messages/inbox-tinyfish.md`
- Modify: `PROTOCOL.md`

**Interfaces:**
- Workflow continues to expose only `TINYFISH_API_KEY` to the worker.
- Queue schema is documented for `from: chatgpt|grok` and `mode: fetch|browser`.

- [ ] **Step 1: Update workflow wording without changing serialization**

Rename the step from fetch-specific wording to shared web worker wording and change commit copy accordingly. Keep `concurrency.group: tinyfish-senses`, `cancel-in-progress: false`, and `contents: write` behavior.

- [ ] **Step 2: Document the queue schema**

Add examples to `messages/inbox-tinyfish.md` for safe fetch and browser tasks, but leave no paid browser task in queued/runnable state.

- [ ] **Step 3: Update `PROTOCOL.md`**

Document TinyFish as shared ChatGPT/Grok web execution infrastructure, with Fetch as default and browser mode explicit/metered. Preserve `state/now.json` as SoT and ChatGPT as decision/merge coordinator.

- [ ] **Step 4: Verify repository text**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: all tests PASS and no repository file contains an API key value.

- [ ] **Step 5: Commit**

Commit message: `docs: wire TinyFish into shared desk protocol`

### Task 6: Verify deployment without spending browser credits

**Files:**
- No product-code changes expected unless verification exposes a defect.

**Interfaces:**
- Existing Fetch route is the live smoke test.
- Browser route is verified only by mocked unit tests until an explicit browser task is later queued.

- [ ] **Step 1: Run full tests**

Run: `python3 -m unittest tests.test_tinyfish_senses -v`
Expected: PASS.

- [ ] **Step 2: Inspect workflow result after deployment**

Confirm GitHub Actions completes successfully for the code/docs push and does not invoke Agent merely because the worker was deployed.

- [ ] **Step 3: Run/requeue one safe existing Fetch task if needed**

Use a public read-only URL and `mode: fetch`; confirm `messages/from-tinyfish.md` records `status: done`, `mode: fetch`, and the correct task/requester metadata.

- [ ] **Step 4: Final verification**

Confirm: no live paid browser run occurred; no duplicate open blocker was created; existing Fetch remains operational; browser code path is covered by mocked tests.

- [ ] **Step 5: Commit only if verification required a fix**

If a defect was fixed, commit it with a focused `fix:` message and rerun the full verification before claiming completion.
