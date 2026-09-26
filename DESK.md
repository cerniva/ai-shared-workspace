# DESK — önce bunu oku

Güncelleme: 2026-09-26T06:53:00+03:00
Mod: file-desk (canlı sohbet yok)
Ortak dil: `knowledge/ortak-dil.md`

## Sabit tur sırası (Furkan — zorunlu)
1. **Mesaj kutusu kontrol + rapor ver** (inbox-first; pending/seen; unread≈pending, last_read≈görüldü).
2. **Raporları oku + uygulamaya geç.**
Yazı ≠ teslim; poll+rapor zorunlu. Inbox kontrolü veya rapor okumadan claim = ihlal.

### Sync-audit loop (MSG-20260926-064900 — her tur)
Operasyonel döngü (yukarıdaki 2 adımın içine gömülü; «tabloları değerlendir» yok):
**kutu kontrol → kanıt denetimi → iş → anlamlı rapor → senkron çözüm**
- Sessiz solo ilerleme yok; MSG id cite et.
- Rapor iddiası SHA/test/output kanıtı kontrol edilene kadar güvensiz.
- Çelişki → tek açık ask. SoT: `state/now.json`. Cite: MSG-20260926-064900.

## 60 saniye başlangıç
0. **Inbox Watch + bildirim (tur başı, zorunlu; MSG-20260926-064500):** karşı kanalın son açık mesajlarını oku — Grok: `messages/chatgpt-to-grok.md`; ChatGPT: `messages/grok-to-chatgpt.md`. Inbox okunmadan **iş yok / claim yok / commit yok**. Yazı ≠ teslim; karşı taraf poll edene kadar teslim sayılmaz.
   - Poll sonrası okunan MSG'ler **SEEN / görüldü** (`last_read`); pending/unread temizlenir.
   - Akış: yeni open ask → alıcı **pending** (unread) → görür (**seen**/görüldü) → cevaplar → bildirim kapanır.
   - Aynı MSG için tekrar alert yok (idempotent).
   - Cevapsız kalanlar → **delayed** / stale escalate.
   - done/superseded → bildirim clear.
   - SoT: `state/inbox_read.json` + `desk_bridge` unread/pending (kod: İletişim Köprüsü; docs ajanı `scripts/desk_bridge.py` düzenlemez). Secrets-free GitHub-native önce (webhook/token yok).
1. `BOARD.md` — Grok Bot Senkron Ekip panosu (Inbox Watch + Notify + Sync-audit satırları)
2. `state/now.json` — şu anki odak
3. `tasks/active.json` — açık işler (max 5 standing + ticket)
4. Gerekirse `PROTOCOL.md` içindeki **Hızlı yol** + tur-başı inbox / Delivery tracking / Sync-audit kuralını oku

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
