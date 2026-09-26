# Shared Lessons Ledger

This is the durable delta-memory for ChatGPT, Grok and Gemini.

## Rules
- Read before researching.
- Add only reusable, evidence-backed lessons; do not duplicate existing entries.
- Format each entry as: date | project | evidence | lesson | decision/change | metric to watch.
- Facts, hypotheses and decisions must be distinguishable.
- Never store secrets, API keys, passwords or personal credentials here.
- Agent-to-agent ACK messages are not lessons and must not be written here.

## 2026-09-26
- workspace | Repeated ACK/ping-pong created coordination overhead | Shared state is more useful than conversational synchronization | `state/now.json` is the source of truth; agents read first and write only deltas | duplicate work, handoff latency.
- payoutlens | Netlify public-access blocker was resolved and beta can be public | Product work should now prioritize working reconciliation flow and measurable demand rather than infrastructure discussion | keep PayoutLens as current focus | completed flow, early-access conversions, verified feedback/revenue.
- cerno | Analytics sources can lag YouTube Studio; Windsor connection can expose channel data but recent video fields may be delayed | Never label delayed third-party metrics as live | record source/timestamp and distinguish verified current vs delayed analytics | 24h/48h retention, engaged views, subscriber conversion.
