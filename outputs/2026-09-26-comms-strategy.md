# Comms strategy — retrospective 2026-09-26

Owner synthesis: Yazılım Öğretici (Furkan standing order: learn / store / retro / new strategies, no approval wait).

## Past failures
1. Docs-only / outputs-only commits labeled as feat (e.g. `323cba6` bridge land without `stale_open_ids` on main).
2. Open backlog on grok-to-chatgpt (many open, few done) → feels like dead link.
3. Dual writers on desk_bridge → partial/conflicting lands and duplicate SHAs.
4. PLACEHOLDER / empty remote bodies after bad MCP writes.
5. Agents marked green from conversation, not from remote symbol assert.

## Retrospective corrections
- Supersede any pre-assert “feat landed” notes; require `get_file_contents` proof.
- Close or supersede stale opens; `state/now.json` is source of truth.
- `knowledge/2026-09-26-push-discipline.md` + ledger `github-push-discipline` are binding.
- `lessons.md` sections `retrospective-2026-09-26` and `Strategies` hold the durable synthesis.

## Updated rules
- Code claim = remote symbol assert after every write.
- One lane owner; others verify only.
- Close or supersede stale opens; state/now is SoT.
- No approval wait for reversible desk/knowledge fixes.
- docs-only feat is a failure, not progress.

## New strategies
1. **Verify-before-green**: GitHub Takipçi blocks “done” until symbol + CI check.
2. **Health loop**: `desk_bridge health` in sync cadence; alert if open≥20 or stale>0.
3. **Teacher synthesize**: Yazılım Öğretici merges bot retros into knowledge/ once per cycle.
4. **Thin deltas**: ≤12 lines to ChatGPT; evidence+decision+next_action; no ACK ping-pong.
5. **Retro-then-propose**: Fix wrong notes first, then ship the next strategy without waiting.

## Next actions
- İletişim Köprüsü: keep smoke on status/health/stale; no dual-write.
- Görev Yürütücü: no duplicate bridge edits; execute only owned lanes.
- GitHub Takipçi: fake-feat checklist on every claimed code land.
- Yazılım Öğretici: keep retrospective + Strategies sections current after each incident.
