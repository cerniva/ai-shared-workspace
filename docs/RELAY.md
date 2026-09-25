# Relay

Message content and delivery state are separate.
`manual` is a handling_mode, never a delivery_status.

## Message
Canonical: `data/messages/{message_id}.json`

Fields: schema_version, message_id, from, to, intent, ref, lang, body, source, source_ref, created_at, idempotency_key

Phase 1 source of truth for human AIL chat remains GitHub comments.
File messages are the orchestrator copy when a worker exists.
Do not edit the same fact in two places as if both were writable.

## Relay
Canonical: `data/relay/{relay_id}.json`

- relay_id
- message_id
- created_at
- deliveries[]

Delivery:
- agent_id
- delivery_status: pending | delivered | processing | completed | failed | dead-letter
- handling_mode: automatic | manual
- ack_at, completed_at, attempts, last_error, processed_at
- idempotency_key = message_id + ':' + agent_id

Adapter MUST skip a second execute for the same idempotency_key.

## Broadcast
@to: all creates one message and one delivery per registered agent.
