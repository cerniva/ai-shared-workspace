# Push disiplini — 2026-09-26

**Kaynak:** Yazılım Öğretici (Furkan emri / Grok Bot)
**Kanıt:** `323cba6` mesajı `feat(desk-bridge)...` ama yalnızca `outputs/*.md` (+1 satır); kod main’de yoktu. Sonra gerçek kod + `stale_open_ids` remote’ta doğrulandı.

## Kök kural
1. **docs-only / outputs-only / messages-only commit’e `feat` veya `fix` demek yasak.** Bunlar `docs(...)` veya `knowledge(...)` olur.
2. Kod iddiası ancak remote `get_file_contents` sonrası sembol assert ile yeşildir.
3. desk_bridge için zorunlu semboller: `stale_open_ids`, CLI `status` / `health` / `stale`.
4. `create_or_update_file` / `push_files` sonrası hemen aynı path’i tekrar oku; SHA + içerik eşleşmezse veya PLACEHOLDER varsa başarısız say, düzelt, yeniden assert et.
5. Aynı commit mesajıyla neredeyse aynı patch’i tekrar push etme (replay).

## Ajan checklist
- [ ] Değişen dosyalar listesinde `scripts/` veya `tests/` var mı?
- [ ] Yoksa mesajda `feat`/`fix` kullanma.
- [ ] Yazımdan sonra remote içerik = yerel içerik?
- [ ] desk_bridge: `stale_open_ids` string remote’ta var mı?

## Metrik
- remote-symbol-miss oranı
- fake-feat count (feat mesajı + sıfır kod dosyası)
- PLACEHOLDER / boş body olayları
