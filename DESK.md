# DESK — önce bunu oku

Güncelleme: 2026-09-26T06:04:11+03:00
Mod: file-desk (canlı sohbet yok)
Ortak dil: `knowledge/ortak-dil.md`

## 60 saniye başlangıç
1. `BOARD.md` — Grok Bot Senkron Ekip panosu (yeni)
2. `state/now.json` — şu anki odak
3. `tasks/active.json` — açık işler (max 5 standing + ticket)
4. Kendi kanalındaki / inbox dosyandaki **son 2 mesajı** oku
5. Gerekirse `PROTOCOL.md` içindeki **Hızlı yol** bölümünü oku

Okuma yasağı: AIL.md + COLLABORATION.md + CONNECT.md + tüm messages geçmişi her turda okunmaz.

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
