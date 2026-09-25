# Security

Hard rules: no secrets in frontend, XSS escape, deny-by-default permissions, mask secrets.

## Authn / Authz (when backend exists)

- Authentication: who sent the request
- Authorization: what that actor may do
- Webhook: signature + timestamp + replay window

## Trust boundary

AI output is untrusted input.
repo.write / publish / delete / external_action require explicit permission AND human approval entity.

approval: required, requested_at, requested_by, approved_by, approved_at, decision, reason

## Audit

Append-only `data/audit/{event_id}.json`

event_id, actor_type, actor_id, action, resource_type, resource_id, timestamp, metadata
