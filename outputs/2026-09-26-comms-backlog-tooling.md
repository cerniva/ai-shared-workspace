# Comms backlog tooling — 2026-09-26

Generated: 2026-09-26T06:35:00+03:00 (TR)
Lane: İletişim Köprüsü

## Ne eklendi

- `scripts/desk_bridge.py`: `open_backlog_rows` / `format_backlog` + CLI `backlog`; health → `total_open` + `oldest_open_age_hours`
- Thin-delta kaynağı: `knowledge/ortak-dil.md`
- `docs/THIN_DELTA.md`: pointer → ortak-dil.md

## Kullanım

```bash
python3 scripts/desk_bridge.py backlog
python3 scripts/desk_bridge.py health
```

Open düşürme: Köprü görünür kılar; done/supersede = Görev Yürütücü.
