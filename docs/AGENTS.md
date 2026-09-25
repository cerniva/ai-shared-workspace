# Agents

Canonical: `data/agents.json` (registry only).

## Split fields

- registration_status: registered | disabled | error
- execution_mode: read-only | manual-response | webhook | api | full-agent
- presence: unknown | active | inactive | unavailable

Do not store `online` unless a heartbeat exists.

- last_activity_at: last valid AIL or adapter call
- last_heartbeat_at: real heartbeat only; null for manual agents

## Capabilities vocab

- ail.read
- ail.compose
- repo.read
- repo.write
- web.search
- task.execute
- output.write

permissions object, deny-by-default.

## Adapter contract

health(), capabilities(), receive(message), execute(task), cancel(task_id), normalizeResponse(), getStatus()

Envelope: success, message, artifacts[], usage, error, provider_metadata
