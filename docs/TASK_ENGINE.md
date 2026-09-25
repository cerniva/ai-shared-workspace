# Task Engine

Canonical file: `data/tasks/{task_id}.json`
GitHub single-file JSON is not a transaction. Writers must use SHA compare and one file per task.

## Fields

schema_version, task_id, parent_task_id, title, description,
assigned_agent, status, dependencies[],
claimed_by, lease_until, attempt,
approval, result, created_at, updated_at

result = { summary, artifacts[], output_refs[], message_refs[] }

## Status

draft | queued | processing | blocked | review | accepted | rejected | done | failed | cancelled | paused

## Allowed transitions

- draft -> queued | cancelled
- queued -> processing | paused | cancelled
- processing -> review | blocked | failed | paused | cancelled
- blocked -> queued | failed | cancelled
- paused -> queued | cancelled
- review -> accepted | rejected | processing
- accepted -> done
- rejected -> queued | cancelled
- failed -> queued | cancelled
- done, cancelled = terminal except human audit override (emits audit event)

Illegal example: done -> processing without audit override.

## Dependencies

- Child stays queued while any dependency is not `done`.
- `accepted` is not enough; `done` resolves a dependency.
- Failed dependency -> child `blocked`.
- Engine MUST reject cycles.

## Lease

Worker sets claimed_by + lease_until before processing.
Expired lease returns task to queued.
