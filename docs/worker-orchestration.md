# AI Worker Orchestration

This layer coordinates ChatGPT, Grok and Gemini through durable GitHub state without pretending GitHub itself wakes external models.

## Components

- `state/work_queue.json`: durable work queue.
- `state/dead_letter.json`: exhausted retry records.
- `scripts/work_queue.py`: state machine, leases and idempotent completion.
- `scripts/worker_adapters.py`: common result contract plus Grok/Gemini adapters.
- `scripts/worker_runner.py`: claim -> provider -> complete/fail flow.
- `scripts/review_gate.py`: ChatGPT accept/reject/merge gate before applied lessons.
- `scripts/run_worker.py`: one-job command line entry point.

## Secrets

Never commit provider credentials. Live workers read only environment variables / secret stores:

- Grok: `XAI_API_KEY`; optional `XAI_MODEL` (default `grok-4.7`).
- Gemini: `GEMINI_API_KEY`; optional `GEMINI_MODEL` (default `gemini-3.6-flash`).

For September 2026 Gemini usage, use a supported Gemini auth key rather than an unrestricted legacy standard key.

## Provider endpoints

- xAI: `POST https://api.x.ai/v1/responses`
- Gemini: `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`

References:
- https://docs.x.ai/developers/rest-api-reference/inference/responses
- https://ai.google.dev/api/generate-content
- https://ai.google.dev/api

## Run

Mock, no credentials:

```bash
python3 scripts/run_worker.py --job JOB_ID --provider grok --mock
```

Live Grok:

```bash
XAI_API_KEY=... python3 scripts/run_worker.py --job JOB_ID --provider grok
```

Live Gemini:

```bash
GEMINI_API_KEY=... python3 scripts/run_worker.py --job JOB_ID --provider gemini
```

## State flow

`queued -> claimed -> completed -> reviewed -> applied`

Failure states: `retryable_failed`, `blocked`, `dead_letter`.

Rules:
- Active claims have a lease; an expired claim can be reclaimed.
- Duplicate completion returns the first result instead of overwriting it.
- Missing credentials become blocked before any provider request.
- Retryable errors are bounded by `max_attempts`.
- Workers cannot self-review or self-apply results.
- Only ChatGPT `accept` / `merge` reviews can become applied lessons.

## Red-team fixes (2026-09-26)

1. **Concurrent claim race** — `work_queue.py` wraps load-modify-save in exclusive `fcntl.flock`. `complete` / `fail` require `worker=` matching the active lease owner; expired leases cannot complete.
2. **Strict JSON** — `worker_adapters.py` requires exactly: `evidence`, `factual_findings`, `hypotheses`, `recommendation`, `confidence`, `next_action`. Missing / wrong type / extra keys → `NonRetryableProviderError`.
3. **Retry / review semantics** — Retryable failures stay `retryable_failed` until `max_attempts`; then `dead_letter`. Non-retryable → `blocked`. `review_gate` never applies on `reject`; only ChatGPT `accept` / `merge` call `mark_applied`.

## Verification

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m compileall -q scripts tests
```

The mock end-to-end test verifies queue -> worker -> ChatGPT review -> lesson promotion without making external provider calls.
