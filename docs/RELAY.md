# Relay

@ref is message_id only. Task linkage is task_id.

## Broadcast

@to: all uses registry snapshot at create time:
recipient_ids[], registry_version, recipient_snapshot_at.
Eligible: registration_status=registered, subscribed=true, not disabled.

## Delivery transitions

pending -> delivered | failed | skipped
delivered -> processing | completed | failed
processing -> completed | failed
failed -> pending | dead-letter
completed, dead-letter, skipped = terminal except human requeue

handling_mode: automatic | manual | observe-only
routing_status: accepted | skipped
skip reason example: capability_missing

ack_at set on delivered.
processed_at set when adapter returns.
completed_at set on completed.
attempts increment on each execute try.
