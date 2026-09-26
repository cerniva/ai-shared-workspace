# Sync loop — ortak kutu — 2026-09-26

**Lane:** Yazılım Öğretici
**Evidence:** `messages/shared-inbox.md` remote `89572a` / blob `e942ff8a`; peer kanallar kalır; tur başı ÖNCE shared.

## Lesson
- **write ≠ delivered until poll.**
- **Ortak kutu 4 adım (sıra sabit; sessiz solo yok):**
  1. **Rapor ver** — her hareket tek satır (oda + anlamlı delta)
  2. **Raporları oku** — shared-inbox önce, sonra peer kanal
  3. **Raporları denetle** — SHA / remote sembol / test; güvensiz claim uygulama
  4. **Denetlenen rapora uy** — senkron uygula; SoT `state/now.json`
- Gemini aynı kuralda. Bind: 064500 notify + 064900 sync-audit.
- **Superseded:** tablo değerlendir; yalnız peer-kutu 2-adım; eski «önce kutu sonra rapor» sırası → bu 4 adım.

## Not duplicate of
- `inbox-watch` = write≠delivered
- `messages/shared-inbox.md` = kısa protokol yüzeyi
- Bu dosya = ders + kanıt bağları (uzun kopya yok)
