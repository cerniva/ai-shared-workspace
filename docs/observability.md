# Worker observability

The worker runtime has an optional, fail-open observability layer in `scripts/observability.py`. Telemetry failure must never fail provider work.

## Local fallback

Set `OBSERVABILITY_LOG_PATH=state/observability.jsonl` to append sanitized JSONL lifecycle events locally. Typical events are `worker.started`, `worker.completed`, `worker.retryable_failed`, `worker.blocked`, and `worker.dead_letter`.

The local file is runtime evidence only and is ignored by git. Its existence does not prove that any external observability service is connected.

## Optional Sentry

Install `scripts/requirements-observability.txt` and provide `SENTRY_DSN` through the runtime secret manager/environment. By default Sentry receives only the sanitized event message. Raw exception objects, which can contain secrets in exception text or stack context, are disabled by default.

Set `SENTRY_CAPTURE_RAW_EXCEPTIONS=1` only after reviewing the workload's data-safety requirements. That opt-in enables raw exception capture/stack traces.

## Optional Langfuse

Install `scripts/requirements-observability.txt` and provide `LANGFUSE_PUBLIC_KEY` plus `LANGFUSE_SECRET_KEY` through the runtime secret manager/environment. Langfuse receives sanitized worker lifecycle metadata as observations. Provider credentials and arbitrary job payloads are not intentionally included in the emitted metadata.

If a self-hosted or non-default Langfuse endpoint is used, configure it using the Langfuse SDK's supported environment settings rather than committing endpoint credentials to the repository.

## Status rules

Do not mark Sentry or Langfuse `verified_connected` merely because code or credentials are present. Promote a service only after a real event is emitted successfully and read back/confirmed in that service. Until then use `available_unverified` (or the applicable blocked/quota status).

## Safety

- Never commit DSNs, API keys, tokens, passwords, or OAuth secrets.
- Secret-like strings are redacted from local/external event metadata before emission.
- External SDK import or delivery failures are swallowed so worker execution remains fail-open.
- PayoutLens is outside this integration and must remain untouched.
