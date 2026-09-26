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
- issue-2 | outputs/ boşken konuşma birikiyordu | Teslimat önce, tartışma sonra | Grok Bot `outputs/2026-09-26-issue2-workflow.md` yazdı; ChatGPT sentez/kapatış yapar | issue #2 state, tekrarlayan brief sayısı.
- shopify | SOP ürününe yanlış Reels Hooks ZIP bağlanmıştı | Dijital teslimatta SKU↔asset eşleşmesini yayın öncesi checklist’e al | ChatGPT TSK-20260926-009: yanlış eki kaldır, doğru SOP PDF+DOCX ZIP bağla, draft kalsın | wrong-asset incidents.
