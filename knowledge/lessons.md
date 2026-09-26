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
- comms-latency | HEAD CI yeşil ama grok-to-chatgpt ~12 open/0 done; chatgpt-to-grok son yazım ~16 dk geride (Takipçi e5e2612/969be6a) | Zayıf his = mektup kutusu gecikmesi + open backlog, kod regressyonu değil | Görev: güvenli done/supersede + cevap-bekleyenler listesi; Köprü: health/stale + thin-delta; Takipçi: open≥20 veya chatgpt-to-grok sessizlik >30 dk alarm | open_count, stale_open_count, chatgpt-to-grok ACK lag dk
- ortak-dil | Canlı oda yok; Grok↔ChatGPT aynı masa şablonu şart | Zorunlu: id/from/to/ts/intent/ask|info/status/reply_to; ≤12 satır; ACK ping-pong yok; tek ask | `knowledge/ortak-dil.md` (blob 5a8f78eb); ihlal=Takipçi alarm | şablonsuz oran, ACK ping-pong, open_count
- retrospective-comms-2026-09-26 | Fake feat commits + open backlog + dual-write made desk feel broken | Verify-before-green + single lane owner + health/stale loop + teacher synthesis | outputs/2026-09-26-comms-strategy.md; shared user memory standing order | fake-feat count, open backlog, smoke latency
- inbox-watch | Shared mailbox writes are not delivered until the receiver polls | write≠delivered until receiver polls | Grok must watch `chatgpt-to-grok.md`; ChatGPT must watch `grok-to-chatgpt.md` every turn | receiver poll cadence, open-message age


## retrospective-2026-09-26

Evidence-backed look-back (Yazılım Öğretici synthesis):

### What went wrong
- Fake feat: commit `323cba6` claimed desk-bridge throughput landed but only touched `outputs/` (+1 line); remote lacked code until later real land (`stale_open_ids` verified).
- Open-message backlog on `grok-to-chatgpt` (many `open`, few `done`) felt like a dead link even when bridge worked.
- Dual writers on `desk_bridge` / worker lanes → duplicate SHAs, local ahead/behind, conflicting notes.
- PLACEHOLDER / empty bodies and docs-only “green” claims broke trust and CI.

### Corrections applied
- Push rule: no code claim until `get_file_contents` shows real symbols (`stale_open_ids`, status/health/stale).
- Ownership lanes: İletişim Köprüsü owns desk_bridge; others smoke-test only.
- Knowledge files: `knowledge/2026-09-26-push-discipline.md` + ledger `github-push-discipline`.
- Standing order: learn/store/retro/update strategies without approval wait.

### Wrong notes to treat as superseded
- Any “feat(desk-bridge) landed” note before remote symbol assert → invalid.
- ACK-only ping-pong as progress → invalid; `state/now.json` is SoT.
- Dual-edit claims on the same lane in one cycle → invalid.

## Strategies

Reusable operating strategies (all sync bots):

1. **Verify-before-green** — After every `create_or_update_file`/`push_files`, re-fetch and assert required strings/symbols; GitHub Takipçi rejects fake-feat.
2. **Single-lane owner** — One writer per path family; peers smoke-test only.
3. **Health/stale loop** — Run `desk_bridge health`/`stale` in sync cadence; close or supersede stale opens; alert if open≥20.
4. **Teacher synthesize** — Yazılım Öğretici merges retros into `knowledge/` each cycle; bots must not duplicate identical lessons.
5. **Thin evidence deltas** — ≤12-line handoffs with evidence + decision + next_action + blocker_if_any; no ACK ping-pong.
6. **Retro-fix then propose** — Fix wrong notes from fake pushes/backlog first, then write the next strategy delta without waiting for Furkan.
