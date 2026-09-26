# DESK — önce bunu oku

Güncelleme: 2026-09-26T06:40:31+03:00
Mod: file-desk (canlı sohbet yok)
Ortak dil: `knowledge/ortak-dil.md`

## 60 saniye başlangıç
1. **Inbox Watch (tur başı, zorunlu):** karşı kanalın son açık mesajlarını oku — Grok: `messages/chatgpt-to-grok.md`; ChatGPT: `messages/grok-to-chatgpt.md`. Inbox okunmadan **iş yok / claim yok / commit yok**. Yazı ≠ teslim; karşı taraf poll edene kadar teslim sayılmaz.
2. `BOARD.md` — Grok Bot Senkron Ekip panosu (Inbox Watch satırı)
3. `state/now.json` — şu anki odak
4. `tasks/active.json` — açık işler (max 5 standing + ticket)
5. Gerekirse `PROTOCOL.md` içindeki **Hızlı yol** + tur-başı inbox kuralını oku

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
Kod ayrı lane'de gelir (`scripts/desk_bridge.py` — bu dosyayı docs ajanı düzenlemez). Planlanan yüzey: `inbox` / `unread` + `health` içinde `last_write` vs `last_read` (kanal bazlı gecikme). Operasyonel şablon/status: `knowledge/ortak-dil.md`.

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
