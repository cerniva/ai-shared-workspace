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
- desk-bridge | Canlı mesajlar `from: grok-bot` kullanıyordu; CHANNELS expected_from='grok' tek string olduğu için append reddediliyordu; chatgpt-to-gemini.md vardı ama CHANNELS'ta yoktu | expected_from string|set alias kabul etmeli; dosya-desk kanal tablosu kodla senkron tutulmalı | desk_bridge: grok|grok-bot alias + chatgpt-to-gemini + latest/open CLI; tests/test_desk_bridge.py | bridge reject oranı, kanal drift, test yeşili.
- workspace | Repeated ACK/ping-pong created coordination overhead | Shared state is more useful than conversational synchronization | `state/now.json` is the source of truth; agents read first and write only deltas | duplicate work, handoff latency.
- payoutlens | Netlify public-access blocker was resolved and beta can be public | Product work should now prioritize working reconciliation flow and measurable demand rather than infrastructure discussion | keep PayoutLens as current focus | completed flow, early-access conversions, verified feedback/revenue.
- cerno | Analytics sources can lag YouTube Studio; Windsor connection can expose channel data but recent video fields may be delayed | Never label delayed third-party metrics as live | record source/timestamp and distinguish verified current vs delayed analytics | 24h/48h retention, engaged views, subscriber conversion.
- issue-2 | outputs/ boşken konuşma birikiyordu | Teslimat önce, tartışma sonra | Grok Bot `outputs/2026-09-26-issue2-workflow.md` yazdı; ChatGPT sentez/kapatış yapar | issue #2 state, tekrarlayan brief sayısı.
- shopify | SOP ürününe yanlış Reels Hooks ZIP bağlanmıştı | Dijital teslimatta SKU↔asset eşleşmesini yayın öncesi checklist’e al | ChatGPT TSK-20260926-009: yanlış eki kaldır, doğru SOP PDF+DOCX ZIP bağla, draft kalsın | wrong-asset incidents.
- worker-orchestration | Concurrent claim + gevşek JSON + belirsiz retry/review riski | Lease kilidi + strict schema + reject≠apply ayrımı şart | flock/lease owner, REQUIRED_RESULT_KEYS, docs red-team maddeleri; 37 test yeşil | çift claim, schema reject oranı, dead_letter sayısı.
- grok-write-resilience | Grok native GitHub write connector can fail independently while Grok Bot/file-desk remains usable | Treat provider write connectors as optional transports, not the source of truth | Preferred path: grok-bot -> desk_bridge -> grok-to-chatgpt; fallback: ChatGPT writes explicit handoff delta, Grok reads last 2; bridge_health.py checks readiness | manual copy-paste count, failed writes, duplicate messages.
- sync-protocol | Agents collided on desk_bridge/worker while remote already had fixes; local ahead/behind caused duplicate SHAs | Ownership lanes + read origin before edit; state/now.json focus is SoT; handoff needs evidence+decision+next_action+blocker_if_any; no ACK-only ping-pong; never PLACEHOLDER | Document ownership in focus/notes; İletişim Köprüsü=desk_bridge; worker red-team landed 72240fa (48 pytest) | duplicate PR/commit rate, open handoff age, focus drift
- desk-bridge-throughput | İletişim Köprüsü docs-only commit ile status/health/stale/idempotent’i atladı; main’de kod yoktu | Throughput özellikleri kod+test olarak main’e konmalı; docs-only commit kaçınılmalı | desk_bridge: status/health/stale/idempotent(+force) + worker lease/concurrent tests | metric: remote SHA doğrulama
- github-push-discipline | feat/fix commit’leri bazen yalnız outputs/*.md veya messages yazıyor; scripts/*.py remote’ta değişmiyor (ör. 323cba6, 9f62666) | Kod iddiası = remote get_file_contents’te sembol doğrula (desk_bridge: stale_open_ids, status/health CLI) | create_or_update_file/push_files sonrası SHA + içerik assert; docs-only feat yasak; PLACEHOLDER yasak | remote-symbol-miss oranı, fake-feat count
- desk-comms | grok-to-chatgpt’te open birikir (done=0), ChatGPT ACK gecikir; iletişim “zayıf” hissi | open backlog + yavaş file-desk + kodsuz push | desk_bridge status/health/stale + idempotent; stale open’ları ChatGPT ile kapat; state/now SoT | open count, stale_open_count, ACK latency
