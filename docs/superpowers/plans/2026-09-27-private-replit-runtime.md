# Private Replit Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a private Replit execution runtime that safely consumes bounded tasks from `cerniva/ai-shared-workspace`, executes only allowlisted v1 operations, and writes sanitized status/results back without exposing credentials or private payloads.

**Architecture:** The public GitHub repository remains the single coordination source. `tasks/runtime-dispatch.json` is a derived execution queue, while `state/runtime-status.json` is the public sanitized execution ledger. A private Replit app polls every 60 seconds, validates each task, records an idempotency state, executes only `read`/`prepare` operations, and writes sanitized results back using optimistic GitHub content updates. Secrets stay only in Replit Secrets.

**Tech Stack:** Python 3.11+, standard library first, GitHub Contents API over HTTPS, `unittest`, Replit private runtime.

**Spec:** `docs/superpowers/specs/2026-09-27-private-replit-runtime-design.md`

## Global Constraints

- `PROTOCOL.md` and `state/now.json` remain the authoritative coordination source.
- `tasks/runtime-dispatch.json` is dispatch-only; it must not become a second source of truth.
- `state/runtime-status.json` contains sanitized execution state only.
- API keys, OAuth tokens, cookies, authenticated session state, customer/order details, and private Shopify/YouTube payloads never enter the public repo.
- v1 enables only `read` and `prepare` actions.
- Payments, purchases, publishing, deletion, permission/account-security changes, credential changes, Shopify writes, YouTube uploads, and general logged-in browser automation remain blocked.
- Poll interval defaults to exactly 60 seconds while the private runtime is running.
- The idempotency key is `<task_id>:<generation>`; the same key must not execute twice after a terminal result.
- The first live acceptance task is synthetic and must not spend model/video credits or touch production Shopify/YouTube data.
- Missing credentials/configuration must fail safely without logging or returning the missing secret value.

## Review Focus

1. **Concurrent GitHub update:** if `runtime-status.json` changes between read and write, the runtime must refetch and retry the state merge rather than overwrite another update.
2. **Duplicate task delivery:** two polling cycles seeing the same `<task_id>:<generation>` must execute the connector once.
3. **Malformed or future-version task:** invalid schema or unsupported contract version must be `blocked` before any connector call.
4. **Secret-looking data in errors:** tokens, Authorization headers, cookies, and configured secret values must be redacted before logs or GitHub write-back.
5. **High-impact operation disguised by connector/operation name:** policy classification must be based on explicit `action_class` plus allowlisted connector/operation pairs; unknown pairs are blocked by default.

---

### Task 1: Add the public runtime contract and seed state

**Files:**
- Create: `tasks/runtime-dispatch.json`
- Create: `state/runtime-status.json`
- Create: `docs/runtime/PRIVATE_RUNTIME_CONTRACT.md`
- Create: `scripts/runtime_contract.py`
- Test: `tests/test_runtime_contract.py`

**Interfaces:**
- Produces: `validate_dispatch_document(data: Any) -> list[str]`
- Produces: `validate_dispatch_item(item: Mapping[str, Any]) -> list[str]`
- Produces: `idempotency_key(item: Mapping[str, Any]) -> str`
- Public dispatch document shape: `{"version": 1, "items": [...]}`.
- Required task fields: `id`, `generation`, `task_type`, `connector`, `operation`, `action_class`, `params`, `created_at`.
- v1 `action_class`: `read` or `prepare` only.
- Public status document shape: `{"version": 1, "items": [...]}`.

- [ ] **Step 1: Write failing contract tests**

Add tests that assert: an empty v1 document validates; the required fields above are enforced; unsupported `version` is rejected; `action_class=write-low-risk` is rejected in v1; `idempotency_key({"id":"A","generation":2}) == "A:2"`; unknown connector/operation pairs are rejected by default.

- [ ] **Step 2: Run the focused test and verify failure**

Run: `python -m unittest tests.test_runtime_contract -v`

Expected: FAIL because `scripts.runtime_contract` and seed documents do not exist yet.

- [ ] **Step 3: Implement the minimal public contract**

Create `scripts/runtime_contract.py` with the exact interfaces above and constants for contract version `1`, allowed action classes `{read, prepare}`, and the initial allowlisted pair `synthetic:echo`.

Create `tasks/runtime-dispatch.json` and `state/runtime-status.json` as version-1 documents with empty `items` arrays.

Document field meaning, status values (`queued`, `running`, `succeeded`, `failed`, `blocked`), idempotency semantics, and the rule that sensitive parameters are resolved only in the private runtime.

- [ ] **Step 4: Run the focused test**

Run: `python -m unittest tests.test_runtime_contract -v`

Expected: PASS.

- [ ] **Step 5: Run related existing tests**

Run: `python -m unittest tests.test_browser_policy tests.test_end_to_end_worker_flow -v`

Expected: PASS; the new contract must not alter the existing worker queue or browser policy.

- [ ] **Step 6: Commit**

Commit message: `feat: add private runtime public contract`

---

### Task 2: Build secret-safe configuration and redaction in the private Replit app

**Files (private Replit app):**
- Create: `runtime/settings.py`
- Create: `runtime/redaction.py`
- Create: `tests/test_settings.py`
- Create: `tests/test_redaction.py`

**Interfaces:**
- Produces: `Settings.from_env(env: Mapping[str, str]) -> Settings`
- Produces: `Settings.ready_for_github -> bool`
- Produces: `redact_text(text: str, secret_values: Iterable[str]) -> str`
- Produces: `sanitize_object(value: Any, secret_values: Iterable[str]) -> Any`
- Required secret/config names: `GITHUB_TOKEN`, `GITHUB_REPO` (default `cerniva/ai-shared-workspace`), `POLL_SECONDS` (default `60`), `RUNTIME_ID` (default `replit-runtime-v1`).

- [ ] **Step 1: Write failing configuration/redaction tests**

Assert: missing `GITHUB_TOKEN` makes `ready_for_github` false without exposing a value; default poll is 60; invalid poll values fail closed to 60; exact configured secret values are replaced with `[REDACTED]`; Authorization/Bearer and cookie-like strings are redacted; nested dict/list sanitization preserves non-sensitive values.

- [ ] **Step 2: Run tests and verify failure**

Run in Replit: `python -m unittest tests.test_settings tests.test_redaction -v`

Expected: FAIL because runtime modules do not exist.

- [ ] **Step 3: Implement configuration and redaction**

Use standard library only. Never print environment values. `Settings` may expose booleans for presence but never secret content in `repr`, health output, or exceptions.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_settings tests.test_redaction -v`

Expected: PASS.

- [ ] **Step 5: Commit inside the private Replit Git workspace if Git is enabled**

Commit message: `feat: add safe runtime configuration`

If the Replit workspace has no Git remote yet, preserve the change in Replit and do not copy secrets or private configuration into the public repo.

---

### Task 3: Add the GitHub Contents client with optimistic concurrency

**Files (private Replit app):**
- Create: `runtime/github_client.py`
- Create: `tests/test_github_client.py`

**Interfaces:**
- Produces: `GitHubContentsClient.get_json(path: str) -> tuple[dict[str, Any], str]` where the second value is the current blob/content SHA.
- Produces: `GitHubContentsClient.put_json(path: str, data: Mapping[str, Any], sha: str, message: str) -> str` returning the new content SHA.
- Produces: `GitHubConflict` for HTTP 409/422 stale-SHA updates.
- All requests target only `Settings.github_repo`; arbitrary repository URLs are not accepted.

- [ ] **Step 1: Write failing HTTP-client tests with mocked transport**

Cover successful GET, successful PUT, missing token, repository mismatch prevention, 404, 401/403 safe errors, stale-SHA conflict, and sanitized error text.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_github_client -v`

Expected: FAIL because client does not exist.

- [ ] **Step 3: Implement the minimal Contents API client**

Use HTTPS requests through the Python standard library. Send `Authorization: Bearer <token>` internally but never include headers/token in raised messages. JSON write-back must include GitHub's current SHA so concurrent changes are detected.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_github_client -v`

Expected: PASS.

- [ ] **Step 5: Commit if the private workspace is Git-backed**

Commit message: `feat: add optimistic github contents client`

---

### Task 4: Implement policy, status ledger, and exactly-once task selection

**Files (private Replit app):**
- Create: `runtime/policy.py`
- Create: `runtime/status_store.py`
- Create: `tests/test_policy.py`
- Create: `tests/test_status_store.py`

**Interfaces:**
- Produces: `classify_task(task: Mapping[str, Any]) -> PolicyDecision`
- Produces: `StatusStore.find(key: str) -> Mapping[str, Any] | None`
- Produces: `StatusStore.begin(task: Mapping[str, Any], now: datetime) -> Mapping[str, Any]`
- Produces: `StatusStore.finish(key: str, *, status: str, summary: str, error_code: str | None, retryable: bool, now: datetime) -> Mapping[str, Any]`
- Produces: `StatusStore.merge_and_write(client: GitHubContentsClient) -> None` with bounded stale-SHA refetch/retry.
- Terminal public statuses: `succeeded`, `failed`, `blocked`.

- [ ] **Step 1: Write failing policy/idempotency tests**

Assert: only `synthetic:echo` with `read` or `prepare` is allowed in v1; any unknown connector or operation is blocked; high-impact action classes are blocked even if operation text looks harmless; terminal idempotency keys are skipped; `running` entries younger than the lease timeout are not re-executed; stale-SHA writes refetch and merge instead of replacing unrelated status rows.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_policy tests.test_status_store -v`

Expected: FAIL.

- [ ] **Step 3: Implement policy and status ledger**

Use `<task_id>:<generation>` as the primary key. `begin()` records `running` before connector execution. Unknown/invalid work is recorded `blocked` without calling any connector. Use a small bounded retry count for GitHub conflict resolution; if conflicts persist, fail the cycle safely rather than overwrite.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_policy tests.test_status_store -v`

Expected: PASS.

- [ ] **Step 5: Commit if Git-backed**

Commit message: `feat: add runtime policy and idempotency ledger`

---

### Task 5: Add the synthetic connector and one-cycle worker

**Files (private Replit app):**
- Create: `runtime/connectors/__init__.py`
- Create: `runtime/connectors/synthetic.py`
- Create: `runtime/worker.py`
- Create: `tests/test_worker.py`

**Interfaces:**
- Produces: `SyntheticConnector.execute(operation: str, params: Mapping[str, Any]) -> Mapping[str, Any]`
- Produces: `RuntimeWorker.cycle(now: datetime | None = None) -> CycleReport`
- Produces: `RuntimeWorker.process(task: Mapping[str, Any], now: datetime) -> Mapping[str, Any]`
- Synthetic operation: `echo`, returning a safe summary of `params.message` only; it performs no network/model/store action.

- [ ] **Step 1: Write failing worker tests**

Cover: valid synthetic task executes once; a second cycle skips the terminal key; malformed task is blocked; unsupported connector is blocked before connector dispatch; connector exception becomes sanitized `failed`; secret text in an exception is redacted; missing GitHub configuration performs no external write and returns a safe blocked/unready cycle result.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_worker -v`

Expected: FAIL.

- [ ] **Step 3: Implement the synthetic connector and cycle**

Cycle sequence is fixed: fetch dispatch -> validate version/schema -> load status -> skip terminal keys -> policy classify -> record `running` -> execute connector -> sanitize -> record terminal result. No connector receives GitHub token or secret values unless its future design explicitly requires them.

- [ ] **Step 4: Run tests**

Run: `python -m unittest tests.test_worker -v`

Expected: PASS.

- [ ] **Step 5: Commit if Git-backed**

Commit message: `feat: add synthetic runtime worker`

---

### Task 6: Add health endpoint, structured logs, and 60-second poll loop

**Files (private Replit app):**
- Create: `runtime/health.py`
- Create: `app.py`
- Create: `tests/test_health.py`
- Create: `tests/test_app_cycle.py`

**Interfaces:**
- Produces: `health_snapshot(worker: RuntimeWorker) -> Mapping[str, Any]`
- Health fields only: `service`, `github_configured`, `github_last_ok`, `last_cycle_at`, `last_success_at`, `runtime_id`.
- `app.py` serves `GET /health` and runs `RuntimeWorker.cycle()` every `POLL_SECONDS` (default 60) while the process is alive.

- [ ] **Step 1: Write failing health/poll tests**

Assert: `/health` contains no token/cookie/private payload; missing GitHub token is reported only as `github_configured: false`; polling uses 60 seconds by default; one cycle exception is logged safely and does not crash the health server; structured log records contain timestamp/task id/connector/operation/status/duration/error code only.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m unittest tests.test_health tests.test_app_cycle -v`

Expected: FAIL.

- [ ] **Step 3: Implement health server and poll loop**

Use standard-library HTTP server/threading. Keep the health server responsive while the worker sleeps. Do not claim 24/7 availability; this is only active while the Replit deployment/process is running.

- [ ] **Step 4: Run all private runtime tests**

Run: `python -m unittest discover -s tests -v`

Expected: PASS.

- [ ] **Step 5: Commit if Git-backed**

Commit message: `feat: add runtime health and polling service`

---

### Task 7: Wire Replit Secrets and run the zero-cost end-to-end acceptance test

**Files:**
- Modify public: `tasks/runtime-dispatch.json`
- Modify public: `state/runtime-status.json` (by the runtime, not hand-edited for the success result)
- Private Replit configuration: secret `GITHUB_TOKEN`; non-secret config `GITHUB_REPO=cerniva/ai-shared-workspace`, `POLL_SECONDS=60`, `RUNTIME_ID=replit-runtime-v1`.

**Interfaces:**
- Acceptance task id: `RUNTIME-SMOKE-20260927-001`
- Generation: `1`
- Connector/operation: `synthetic` / `echo`
- Action class: `prepare`
- Safe params: `{"message":"runtime bridge smoke test"}`
- Expected idempotency key: `RUNTIME-SMOKE-20260927-001:1`

- [ ] **Step 1: Configure the Replit secret without exposing it in chat or GitHub**

`GITHUB_TOKEN` must be a least-privilege credential that can read the approved public coordination files and update only the approved dispatch/status files. Do not paste the token into chat, source code, logs, or the public repository.

- [ ] **Step 2: Verify health before enabling the smoke task**

Open `/health` and confirm: service is up, `github_configured=true`, no secret value is present, and GitHub connectivity becomes healthy after a successful read cycle.

- [ ] **Step 3: Add the synthetic dispatch item to the public queue**

Append exactly one task with the acceptance fields above and a valid `created_at` timestamp.

- [ ] **Step 4: Observe the first execution**

Expected public ledger transition for key `RUNTIME-SMOKE-20260927-001:1`: `running` -> `succeeded`, with a sanitized summary and timestamps. No model/video/store connector should be invoked.

- [ ] **Step 5: Prove duplicate suppression**

Allow at least one additional polling cycle or invoke another cycle manually. Expected: the same idempotency key remains terminal and no second connector execution is recorded.

- [ ] **Step 6: Prove fail-closed behavior**

Add or locally inject a disallowed test task such as connector `synthetic`, operation `publish`, action class `write-low-risk`. Expected: `blocked` before connector execution.

- [ ] **Step 7: Run regression tests in the public repo**

Run: `python -m unittest discover -s tests -v`

Expected: PASS.

- [ ] **Step 8: Record verified status**

Update `docs/MULTI_AGENT_AUTOMATION_STATUS.md` with only observed facts: private Replit v1 runtime status, smoke task result, duplicate-suppression proof, and remaining blockers. Do not claim permanent 24/7 operation.

- [ ] **Step 9: Commit public verification artifacts**

Commit message: `verify: prove private Replit runtime bridge`

---

## Self-Review Notes

- Spec coverage: public/private boundary, secrets, allowlist, idempotency, retries/conflicts, health, logging, synthetic acceptance, and high-impact blocks are all mapped to tasks.
- Existing `state/work_queue.json` / `scripts/work_queue.py` remain untouched; the runtime dispatch file is a derived execution boundary, not a replacement queue for existing AI worker jobs.
- Existing `scripts/policy_gate.py` remains unchanged in v1; the private runtime uses a stricter connector/operation allowlist rather than weakening the existing browser policy.
- No external paid connector is required to pass v1.
- The only user-secret setup step is adding the least-privilege GitHub credential to Replit Secrets; its value is never requested in chat.
