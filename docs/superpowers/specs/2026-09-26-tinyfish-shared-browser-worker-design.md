# TinyFish Shared Browser Worker — Design

Date: 2026-09-26
Status: approved in chat; written-spec review pending

## Intent

Turn the existing TinyFish desk integration into a shared web execution layer for ChatGPT and Grok. Both agents should be able to enqueue web work through the GitHub desk and read the same result channel, while keeping the current free Fetch path intact.

Success means:
- ChatGPT or Grok can write a task to `messages/inbox-tinyfish.md`.
- `mode: fetch` continues to use TinyFish Fetch for read-only page extraction.
- `mode: browser` can use TinyFish Agent browser automation for navigation/click/form workflows.
- Results land in `messages/from-tinyfish.md` with task id, mode, status and bounded output.
- Failures that genuinely require Furkan (missing secret, auth/profile, credits) create one actionable blocker instead of duplicate alerts.

## Current State

The repository already has `.github/workflows/tinyfish-senses.yml` and `scripts/tinyfish_senses.py`. The current worker is intentionally fetch-only and uses `TINYFISH_API_KEY`. The same TinyFish developer platform exposes Agent endpoints; the synchronous browser endpoint is `POST https://agent.tinyfish.ai/v1/automation/run` with `X-API-Key` authentication.

## Chosen Architecture

Keep one shared queue and one result channel. Extend the existing worker rather than adding a second bot or parallel desk.

Task contract:

```text
## TASK
status: queued
id: <stable task id>
from: chatgpt|grok
mode: fetch|browser
url: https://...
goal: |
  <plain-language goal>
```

For compatibility, the worker also accepts the existing `urls:` field for `mode: fetch`. Missing `mode` defaults to `fetch`, so existing tasks do not break.

Execution routing:
- `fetch`: existing `https://api.fetch.tinyfish.ai` path, up to 10 URLs, read-only.
- `browser`: TinyFish Agent synchronous `/v1/automation/run`, one start URL and one goal, `browser_profile: lite`, bounded with `max_steps: 50` and `max_duration_seconds: 300`.

Output contract:

```text
---
id: <result id>
task_id: <input task id>
from: tinyfish
requested_by: chatgpt|grok
mode: fetch|browser
status: done|blocked|failed
created_at: <UTC ISO-8601>
---
<bounded JSON/result>
```

## Safety and Cost Boundaries

Browser mode is an execution tool, not blanket authority. The shared worker may navigate public sites, click, and fill non-sensitive forms needed for an explicit task. It must not autonomously purchase/pay, publish externally, delete data, change account/security settings, submit secrets, or bypass login/2FA/CAPTCHA.

The GitHub worker will not store credentials in repository files. `TINYFISH_API_KEY` remains a GitHub Actions secret. Authenticated browser-profile/vault work is not enabled in this first version; a task that needs login/profile state becomes `blocked` with one human-action record.

Because TinyFish Agent/browser automation may be metered, browser mode must not silently fall back from free Fetch. Only an explicit `mode: browser` task can invoke the Agent endpoint. Insufficient-credit/subscription responses are reported as blockers; the worker does not retry-spend automatically.

## Queue and Ownership

`messages/inbox-tinyfish.md` is shared infrastructure, not owned by one agent. ChatGPT and Grok may enqueue tasks. `messages/from-tinyfish.md` is append-only worker output. `state/now.json` remains the system source of truth for overall work; TinyFish does not become a decision-maker.

Only the latest queued task is executed in v1, matching the current worker behavior. Concurrency remains serialized by the existing GitHub Actions concurrency group to avoid two workers rewriting the same inbox/result files.

## Error Handling

- Missing `TINYFISH_API_KEY`: mark task blocked and create/dedupe a user-action record.
- Invalid/missing URL or unsupported mode: mark failed locally; do not ask the user for a secret.
- TinyFish 401/403: blocker for API key/permission.
- TinyFish 402/credit/subscription condition: blocker for credits/plan; no automatic retry.
- TinyFish 429/5xx: mark blocked/retryable with diagnostic note; no unbounded retry loop.
- Login/2FA/CAPTCHA/profile requirement: blocked and handed to user rather than bypassed.
- Result output is size-bounded before commit.

## Files

Modify:
- `scripts/tinyfish_senses.py` — parse mode/from/id/url/goal, route Fetch vs Agent, normalize output, dedupe blockers.
- `.github/workflows/tinyfish-senses.yml` — rename step/commit copy from fetch-only to shared web worker; keep secret and serialized execution.
- `messages/inbox-tinyfish.md` — document the shared task schema without queuing a paid browser run automatically.
- `PROTOCOL.md` — document TinyFish as shared web execution infrastructure for ChatGPT/Grok.

Create:
- `tests/test_tinyfish_senses.py` — unit tests for parsing, default fetch compatibility, browser request construction, prohibited action guard, and blocker dedupe.

## Verification

1. Unit tests pass without network access.
2. Existing fetch task format still parses and routes to Fetch.
3. Browser task builds the documented TinyFish Agent request but tests mock the network, so verification itself does not consume Agent credits.
4. Existing live Fetch path remains operational with the configured secret.
5. No live paid browser smoke test is triggered merely by deploying the code; a later explicit browser task is the first metered run.
