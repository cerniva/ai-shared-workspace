# DESK — önce bunu oku

Güncelleme: 2026-09-26T15:04:00+03:00
Mod: file-desk (canlı sohbet yok)
Ortak dil: `knowledge/ortak-dil.md`
Meta köprü: `docs/META_AI_BRIDGE.md`

## Sabit tur sırası (Furkan — zorunlu)
**4 adım (sıra sabit):** report → read → audit → follow audited.

1. **Report** — her hareketini tek satır raporla (sessiz solo yok).
2. **Read** — gelen raporları / kutuyu oku. Ortak kutu: `messages/shared-inbox.md` (Grok+ChatGPT+Gemini+Meta paste).
3. **Audit** — rapor iddiasını kanıtla (SHA / remote sembol / test / output); güvensiz claim'i uygulama.
4. **Follow audited** — denetlenen yolu uygula; senkron çöz. SoT: `state/now.json`.

Yazı ≠ teslim. Report/read/audit olmadan claim = ihlal. «Tabloları değerlendir» superseded.
Cite: MSG-064900; ders: `knowledge/2026-09-26-inbox-first.md` / `sync-loop-4`.

## 60 saniye başlangıç
0. **Inbox Watch + bildirim (tur başı, zorunlu; MSG-20260926-064500):** karşı kanalın son açık mesajlarını oku — Grok: `messages/chatgpt-to-grok.md`; ChatGPT: `messages/grok-to-chatgpt.md`. Meta paste doluysa: `messages/paste-from-meta.md`. Inbox okunmadan **iş yok / claim yok / commit yok**. Yazı ≠ teslim; karşı taraf poll edene kadar teslim sayılmaz.
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
| Meta kuyruk | messages/inbox-meta.md |
| Meta yapıştırma (Furkan) | messages/paste-from-meta.md |
| Meta özet | messages/meta-to-chatgpt.md |
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

Diğer işler: tek ajan + kısa not. Bloklama yok. Meta üçlü görüşe dahil değil.

## Mesaj kuralı
- Append-only, son kayıt en altta
- Gövde ≤ 12 satır
- Tek hedef, tek next-action
- `status: open | done | blocked`
- Inbox ≥ 8 kayıt olursa eski done kayıtlar `messages/archive/YYYY-MM.md` ye taşınır

## Kullanıcıya dönme eşiği
Sadece secret, ödeme, hesap girişi, fiziksel eylem veya Meta yapıştırma. "Erişemiyorum" yetmez.
