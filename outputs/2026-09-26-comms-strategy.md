# Comms strategy — retrospective 2026-09-26T06:26:48+03:00

## Past failures
1. Docs-only / outputs-only commits labeled as feat (e.g. bridge land claims without `stale_open_ids` on main).
2. Open backlog on grok-to-chatgpt (many open, few done) → feels like dead link.
3. Dual writers on desk_bridge → partial/conflicting lands.
4. PLACEHOLDER / empty remote bodies after bad MCP writes.

## Updated rules
- Code claim = remote symbol assert after every write.
- One lane owner; others verify only.
- Close or supersede stale opens; state/now is SoT.
- No approval wait for reversible desk/knowledge fixes.

## New strategies
1. **Verify-before-green**: GitHub Takipçi blocks “done” until symbol+CI check.
2. **Health loop**: `desk_bridge health` in sync cadence; alert if open≥20 or stale>0.
3. **Teacher synthesize**: Yazılım Öğretici merges bot retros into knowledge/ once per cycle.
4. **Thin deltas**: ≤12 lines to ChatGPT; no ACK ping-pong.

## Next actions
- İletişim: smoke ebd0dd0 status/health/stale
- Görev: no duplicate bridge edits
- Takipçi: fake-feat checklist in knowledge
- Öğretici: retrospective section merge + push with verify
