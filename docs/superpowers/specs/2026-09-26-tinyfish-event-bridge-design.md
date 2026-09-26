# TinyFish Event Bridge Design

Date: 2026-09-26
Status: proposed / awaiting implementation-plan approval

## Intent

Increase coordination speed between ChatGPT, Grok, Gemini, Meta, and the existing GitHub shared desk by using TinyFish as the team's web execution and event source, without replacing GitHub as the source of truth.

Success means: a web task has one durable task ID, starts once, reports meaningful lifecycle changes, deposits evidence in the shared desk, routes the result to the requesting agent, and does not require wasteful polling or duplicate browser runs.

## Existing system to preserve

- GitHub files remain durable source of truth for tasks, messages, state, and evidence.
- `messages/inbox-tinyfish.md` is the TinyFish request queue.
- `messages/from-tinyfish.md` is the TinyFish result channel.
- `scripts/tinyfish_senses.py` already supports free `fetch` and guarded `browser` modes.
- `.github/workflows/tinyfish-senses.yml` executes the shared TinyFish worker with `TINYFISH_API_KEY` from GitHub Secrets.
- Existing safety gates remain: no payment/purchase, public publish, destructive account action, security credential changes, secret exposure, login bypass, or 2FA/CAPTCHA bypass through autonomous browser goals.

## Chosen architecture

Use an event-bridge extension rather than replacing the current worker.

Flow:

1. ChatGPT/Grok/Gemini/Meta creates a normalized TinyFish task with `task_id`, `requested_by`, `mode`, target URL(s), goal, and status.
2. `tinyfish_senses.py` validates safety, allowlists, and idempotency before external execution.
3. `fetch` stays the default low-cost path for read-only extraction.
4. Explicit `browser` tasks create a TinyFish Agent run. The run ID is persisted immediately so the same task cannot start a second browser run while the first is active.
5. Lifecycle events are normalized as `queued`, `running`, `done`, `blocked`, or `failed` and written as meaningful deltas, not heartbeat spam.
6. Results/evidence are appended to `messages/from-tinyfish.md`; durable run metadata is stored under `state/` so later workers can reconcile after restarts.
7. A router maps `requested_by` to the relevant agent inbox/handoff. The shared desk remains authoritative even if direct notification fails.
8. `state/now.json` receives only concise blocker/next-action deltas for active CORE work.

## Event delivery strategy

### Phase 1 — GitHub-native event bridge

Implement immediately without requiring a new public server or secret:

- Persist TinyFish `run_id` and task state.
- Reconcile active runs through a bounded GitHub Actions workflow.
- Trigger routing when status changes.
- Deduplicate by `task_id + run_id + terminal_status`.
- Do not create ACK-only messages.

This improves reliability using infrastructure already available in the repository.

### Phase 2 — webhook fast path

TinyFish Agent supports `webhook_url`, but a webhook needs a stable HTTPS receiver. Add webhook delivery only when an authenticated receiver exists. The webhook is an acceleration path, not the source of truth: every event is still reconciled against persisted run state.

This avoids inventing a public endpoint or adding infrastructure solely for speed before it is needed.

## Routing

Normalized requester values:

- `chatgpt` -> ChatGPT handoff/inbox
- `grok` -> Grok handoff/inbox
- `gemini` -> Gemini inbox
- `meta` -> Meta inbox

A TinyFish completion should contain:

- task ID
- TinyFish run ID when applicable
- requester
- mode
- terminal status
- concise result/evidence pointer
- blocker if any
- exactly one next action when work remains

The router must not recursively retrigger the same TinyFish task from its own completion message.

## Idempotency and concurrency

- One active external browser run per task ID.
- Persist run ID before waiting for completion.
- A rerun of GitHub Actions first checks persisted state.
- Terminal tasks are not executed again unless a new task ID is created.
- Event routing uses a deterministic event key and ignores already-recorded keys.
- Existing workflow concurrency stays enabled; event reconciliation gets its own concurrency group.

## Failure handling

- 401/403: create one open API/permission blocker; no retry storm.
- 402: create one credits/plan blocker; do not silently fall back to weaker automation.
- 429/5xx: mark retryable with bounded backoff; no duplicate run creation.
- timeout/unknown state: preserve run ID and reconcile; never assume failure means the remote run stopped.
- malformed task: fail locally without external call.

## Cost and speed policy

- Prefer free TinyFish Search/Fetch for reading public pages.
- Use metered browser automation only when clicks/forms/navigation are necessary.
- Never use browser automation merely to poll a page that Fetch can read.
- Cache/reuse evidence when the target has not changed.
- Route only meaningful deltas to agents.

## Security

- `TINYFISH_API_KEY` remains GitHub Secret only.
- No secrets in task files, outputs, logs, or prompts.
- Browser goals remain subject to the existing prohibited-action gate.
- Login/OAuth/2FA/identity verification, spending, supplier orders, destructive actions, and other high-risk writes remain human-gated.
- PayoutLens remains untouched unless explicitly requested.

## Proposed files

Expected implementation may touch:

- `scripts/tinyfish_senses.py` — run-state/idempotency and nonblocking browser-start behavior
- `scripts/tinyfish_event_bridge.py` — reconciliation, event normalization, routing, dedupe
- `.github/workflows/tinyfish-senses.yml` — persist relevant state files
- `.github/workflows/tinyfish-event-bridge.yml` — bounded reconciliation trigger
- `state/tinyfish-runs.json` — durable run/event ledger
- tests for parsing, idempotency, routing, retries, and safety
- documentation for task/event schema

Exact file split can be adjusted during implementation planning if existing orchestration utilities should be reused instead of duplicated.

## Verification

Implementation is complete only when automated tests prove:

1. duplicate workflow execution cannot create a second browser run for the same task;
2. Fetch tasks still work as before;
3. browser run IDs persist before reconciliation;
4. a terminal TinyFish result routes once to the correct requester;
5. retryable errors do not create user-action spam;
6. payment/login/destructive goals remain blocked;
7. no live metered browser call is required by the test suite;
8. GitHub Actions syntax and Python compilation/tests pass.

A real browser smoke test is optional and should only be run when it provides new evidence rather than spending credits for a redundant check.
