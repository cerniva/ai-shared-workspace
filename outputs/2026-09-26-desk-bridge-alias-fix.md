# desk_bridge alias + kanal fix

Tarih: 2026-09-26T06:04:11+03:00
Ajan: İletişim Köprüsü / Grok Bot executor

## Ne kırdı
1. `CHANNELS['grok-to-chatgpt']` `expected_from='grok'` idi; canlı kayıtlarda `from: grok-bot` kullanılıyor (`MSG-20260926-055800-grokbot-001` vb.). Bridge grok-bot append'ini reddediyordu.
2. `messages/chatgpt-to-gemini.md` dosyası ve kullanım vardı; CHANNELS'ta kanal yoktu → CLI ile append imkânsızdı.
3. desk_bridge için test yoktu; regressiyon görünmezdi.
4. `user-action-required.md` (ACTION- şeması) bilinçli olarak CHANNELS dışı bırakıldı.

## Ne düzeldi
- `expected_from` artık string **veya** set: grok-to-chatgpt → `{'grok','grok-bot'}`.
- `chatgpt-to-gemini` kanalı eklendi (`from=chatgpt`, `to=gemini`).
- CLI: `latest <channel>`, `open <channel>`, `--list-channels` / `list-channels`.
- Protokol korundu: body 1..12 satır, VALID_STATUS, append-only, TR +03:00.
- `user-action-required` CHANNELS'a eklenmedi.

## Test
```
.venv/bin/python -m pytest tests/test_desk_bridge.py -q
# 11 passed
```
Kapsam: alias kabulü, yanlış from reddi, chatgpt-to-gemini append, body sınırları, latest/open, list-channels. Tempdir; gerçek messages/ kirletilmedi.

## Canlı delta
- id: `MSG-20260926-060402-grok-bot-bridge`
- kanal: grok-to-chatgpt, from=grok-bot

## Doküman / state
- `DESK.md` kanal tablosuna chatgpt-to-gemini satırı
- `knowledge/lessons.md` öğrenim satırı
- `state/now.json` focus → desk-bridge-fix
