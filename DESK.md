# DESK — önce bunu oku

Güncelleme: 2026-09-26T06:46:13+03:00
Mod: file-desk (canlı sohbet yok)
Ortak dil: `knowledge/ortak-dil.md`

## 60 saniye başlangıç
**Sıra sabit (Furkan standing order):** önce gelen kutu, sonra panolar — tersine çevrilemez.

0. **Inbox first (zorunlu):** karşı kanalın son open kayıtlarını oku + **tek satır rapor** (ör. `inbox: chatgpt-to-grok open=N stale=M`). Grok → `messages/chatgpt-to-grok.md`; ChatGPT → `messages/grok-to-chatgpt.md`. Inbox okunmadan **iş yok / claim yok / commit yok**. Yazı ≠ teslim.
1. **Tables / APPLY:** `BOARD.md` + `state/now.json` + `tasks/active.json` oku ve **uygula** (yalnızca okuma değil).
2. Gerekirse `PROTOCOL.md` **Hızlı yol** + Inbox Watch.
3. Knowledge: `knowledge/lessons.md` (inbox-first-then-tables).

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
CLI (landed/WIP): `inbox|unread` (+ `--mark`); delivery `pending|seen|answered|delayed` (GitHub-native). **Protokol:** mesaj bırakmak yetmez → teslim/görüldü takip. Şablon: `knowledge/ortak-dil.md`. Ders: `knowledge/lessons.md`.

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
