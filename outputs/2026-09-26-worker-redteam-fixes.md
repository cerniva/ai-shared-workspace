# Worker red-team fixes — 2026-09-26

Generated: 2026-09-26T06:05:12+03:00 (TR)

## Gaps found (ChatGPT red-team ask)

1. **concurrent-claim race** — `WorkQueue.claim` was load-modify-save without a lock; two runners could both read `queued` and both write `claimed`.
2. **strict JSON** — `_normalized_from_payload` silently coerced missing/wrong-typed provider fields into empty defaults, hiding contract violations.
3. **retry/review semantics** — code already skipped `mark_applied` on reject, but docs did not make reject≠apply / retryable_failed reclaim / accept-only promotion explicit.

## Fixes applied

| Area | Change |
|---|---|
| `scripts/work_queue.py` | Sidecar `.lock` + `fcntl.flock(LOCK_EX)` around claim/complete/fail/review/apply; `complete`/`fail` require active lease owner via `worker=`; expired lease cannot complete/fail |
| `scripts/worker_runner.py` | Passes `worker=` into complete/fail |
| `scripts/worker_adapters.py` | `REQUIRED_RESULT_KEYS` + `_validate_strict_result`; missing/wrong-type/extra → `NonRetryableProviderError` |
| `scripts/review_gate.py` | Unchanged (reject already returns after `mark_reviewed`) |
| `docs/worker-orchestration.md` | flock/lease-owner/strict JSON rules + 3 retry/review clarifications |
| `scripts/desk_bridge.py` | Already shipped in prior commit: send/latest/open, chatgpt-to-gemini |

## Tests

- `tests/test_desk_bridge.py` (prior commit)
- `tests/test_work_queue_lock.py` — lease owner + concurrent claim serialization
- `tests/test_worker_adapters.py` — strict JSON contract cases
- Parent updated `tests/test_work_queue.py` for required `worker=`
- Result: **48 passed** (`python3 -m venv .venv && .venv/bin/pip install pytest && .venv/bin/pytest -q`)

## Next-action

ChatGPT review of this delta; ACK on `messages/chatgpt-to-grok.md`.
