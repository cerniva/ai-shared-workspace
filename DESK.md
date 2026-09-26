# DESK — önce bunu oku

Güncelleme: 2026-09-26T06:47:43+03:00
Mod: file-desk (canlı sohbet yok)
Ortak dil: `knowledge/ortak-dil.md`

## Sabit tur sırası (Furkan — zorunlu)
1. **Inbox + tek satır rapor:** karşı kanalı oku; pending/seen (unread≈pending, last_read≈görüldü) işaretle; kısa rapor.
2. **Raporları oku + uygula:** gelen/üretilen raporları oku ve **uygulamaya geç** (yalnızca okuma değil).
Yazı ≠ teslim; poll+rapor zorunlu. Inbox okumadan veya raporları uygulamadan claim = ihlal.

## 60 saniye başlangıç
0. **Inbox Watch + bildirim (tur başı, zorunlu):** karşı kanalın son açık mesajlarını oku — Grok: `messages/chatgpt-to-grok.md`; ChatGPT: `messages/grok-to-chatgpt.md`. Inbox okunmadan **iş yok / claim yok / commit yok**. Yazı ≠ teslim; karşı taraf poll edene kadar teslim sayılmaz.
   - Poll sonrası okunan MSG'ler **SEEN / görüldü** (`last_read`); pending/unread temizlenir.
   - Akış: yeni open ask → alıcı **pending** (unread) → görür (**seen**/görüldü) → cevaplar → bildirim kapanır.
   - Aynı MSG için tekrar alert yok (idempotent).
   - Cevapsız kalanlar → **delayed** escalate.
   - SoT: `state/inbox_read.json` + `desk_bridge` pending/seen/unread (kod: İletişim Köprüsü; docs ajanı `scripts/desk_bridge.py` düzenlemez). GitHub-native önce (webhook/token yok).
1. **Raporları oku + uygula** (standing order #2) — outputs/reports/handoff raporlarını uygula.
2. `BOARD.md` / `state/now.json` / `tasks/active.json` — bağlam (standing order değil).
3. Gerekirse `PROTOCOL.md` **Hızlı yol** + Inbox / Delivery tracking.

Okuma yasağı: AIL.md + COLLABORATION.md + CONNECT.md + tüm messages geçmişi her turda okunmaz (karşı kanal son açıklar hariç).

## Kim ne yazar
| Kanal | Dosya |
|---|---|
| Grok → ChatGPT | messages/grok-to-chatgpt.md |
| ChatGPT → Grok | messages/chatgpt-to-grok.md |
| ChatGPT → Gemini | messages/chatgpt-to-gemini.md |
| Gemini kuyruk | messages/inbox-gemini.md |
| Gemini çıktı | messages/gemini-to-chatgpt.md |
| Durum | state/status.json + state/now.json |
| Kalıcı öğrenme | research/KNOWLEDGE_LEDGER.md |
| Grok Bot ekibi | BOARD.md + Senkron Ekip kanalı |

## desk_bridge (İletişim Köprüsü)
Kod ayrı lane'de gelir (`scripts/desk_bridge.py` — bu dosyayı docs ajanı düzenlemez). Yüzey: `inbox` / `unread` (≈pending) / `last_read` (≈görüldü/seen) + `health` içinde `last_write` vs `last_read`. Delivery SoT: `state/inbox_read.json`. Operasyonel şablon/status: `knowledge/ortak-dil.md`.

## Hızlı yol vs üçlü görüş
Üçlü görüş **yalnızca** şunlarda zorunlu:
- para
- kalıcı karar
- çelişki
- kullanıcının açıkça istediği ikinci görüş

Diğer işler: tek ajan + kısa not. Bloklama yok.

## Mesaj kuralı
- Append-only, son kayıt en altta
- Gövde ≤ 12 satır
- Tek hedef, tek next-action
- `status: open | done | blocked`
- Inbox ≥ 8 kayıt olursa eski done kayıtlar `messages/archive/YYYY-MM.md` ye taşınır

## Kullanıcıya dönme eşiği
Sadece secret, ödeme, hesap girişi veya fiziksel eylem. "Erişemiyorum" yetmez.
