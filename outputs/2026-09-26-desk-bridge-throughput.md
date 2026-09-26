# desk-bridge throughput — 2026-09-26

Generated: 2026-09-26T06:20:00+03:00 (TR)
Owner: gorev_yurutucu (Furkan onayı yok — main’e uygulandı)
PayoutLens: dokunulmadı

## Added (`scripts/desk_bridge.py`)

- `channel_status(channel)` → total/open/done/blocked/queued + latest_id/created_at/path
- `channel_health(channel|None)` → per-channel status + problems (missing file, open_count high, stale opens)
- `stale_open_ids(channel, older_than_hours=24)` → open + created_at < now-TR − hours
- `append_message(..., force=False)` → idempotent on normalize(body)+from+to+status=open; `--force` bypass
- CLI: `status <channel>`, `health`, `stale <channel> [--hours 24]`, send `--force`
- `STALE_HOURS = 24` (bridge_health.py ayrı JSON health — korundu)

## Tests

- `tests/test_desk_bridge.py`: idempotent, force, status, stale, health
- `tests/test_work_queue.py`: concurrent claim (multiprocessing + SlowSaveQueue 0.15s), wrong-worker complete/fail, expired-lease complete

## Run

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m compileall -q scripts tests
python3 scripts/desk_bridge.py status grok-to-chatgpt
python3 scripts/desk_bridge.py health
python3 scripts/desk_bridge.py stale grok-to-chatgpt --hours 24
```

## Next-action

CI yeşil + ChatGPT ACK; stale open handoff’ları now.json ile kapat.
