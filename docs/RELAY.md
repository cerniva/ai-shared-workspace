# Relay / Message Bus

Relay is how agents notice work. It is not magic presence.

## Event

```
relay_id
ail_id
from
to            # agent id or all
intent
status        # pending | delivered | processing | completed | failed
created_at
ack_at
```

## Routing

- @to: grok -> only grok adapter
- @to: chatgpt -> only chatgpt adapter
- @to: all -> every registered agent in its own mode

## Phase 1 transport

GitHub issue comments + `data/relay.json`
Polling is honest. WebSocket is future.

If an agent has no write adapter, status stays `pending` or `manual` until a human posts the AIL text.
