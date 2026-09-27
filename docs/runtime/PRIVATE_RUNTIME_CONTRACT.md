# Private Runtime Public Contract

Version: 1

This document defines the only public coordination surface used by the private Replit runtime. It does not make the public repository a secret store or a second task database.

## Dispatch

`tasks/runtime-dispatch.json` has shape:

```json
{"version": 1, "items": []}
```

Each item requires these non-sensitive fields:

- `id`: stable task id.
- `generation`: integer revision starting at 1.
- `task_type`: non-sensitive task category.
- `connector`: allowlisted connector name.
- `operation`: allowlisted operation name.
- `action_class`: v1 allows only `read` or `prepare`.
- `params`: non-sensitive parameters only.
- `created_at`: creation timestamp.

The v1 allowlist initially contains only `synthetic:echo` so the bridge can be proven without model, video, Shopify, YouTube, payment, publishing, browser-login, or other production side effects.

## Idempotency

The public idempotency key is `<id>:<generation>`. A terminal result for that key means the private runtime must not execute the same generation again.

## Status

`state/runtime-status.json` also uses `{ "version": 1, "items": [...] }`.

Public status values are:

- `queued`
- `running`
- `succeeded`
- `failed`
- `blocked`

Result rows may include safe timestamps, a human-readable sanitized summary, an error code, a retryable boolean, and a non-sensitive public artifact/reference URL.

## Sensitive data boundary

Public dispatch/status files must never contain API keys, OAuth tokens, Authorization headers, cookies, authenticated session state, customer/order data, private Shopify/YouTube payloads, or raw private-service request/response bodies.

Sensitive values are resolved only inside the private runtime from Replit Secrets or another approved private connector. Logs and public write-back must redact secret material.

## v1 policy

Unknown connector/operation pairs are blocked by default. High-impact writes such as payments, purchases, publishing, deletion, account-security changes, permission changes, credential changes, Shopify writes, YouTube uploads, and logged-in browser automation are outside v1.
