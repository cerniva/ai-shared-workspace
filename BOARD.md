# Ortak pano — Senkron Ekip

Güncelleme: 2026-09-26T06:50:00+03:00
Kurulum: Grok Bot (Senkron Ekip kanalı)

## Amaç
ChatGPT ↔ Grok (ve botlar) aynı panoda çalışır. Canlı model sohbeti yok; kaynak gerçek: bu repo.

## Sabit tur sırası (Furkan — zorunlu)
1. Mesaj kutusu kontrol + rapor ver (pending/seen; unread≈pending, last_read≈görüldü)
2. Raporları oku + uygulamaya geç
Yazı ≠ teslim; poll+rapor zorunlu. Inbox kontrolü veya rapor okumadan claim = ihlal.

## Inbox Watch (zorunlu gate)
| Adım | Kural |
|---|---|
| Inbox Watch | Her tur başı karşı kanalı oku: Grok → `messages/chatgpt-to-grok.md`; ChatGPT → `messages/grok-to-chatgpt.md`. Bu turda inbox okunmadan **iş yok / claim yok / commit yok**. Yazı ≠ teslim (karşı taraf poll edene kadar). |
| Notify / pending / delayed | Yeni open ask → alıcı **pending** (unread); poll+okuma → **seen** (görüldü / last_read); cevap/done → bildirim kapanır. Aynı MSG tekrar alert yok. Cevapsız → **delayed** escalate. SoT: `state/inbox_read.json` + desk_bridge pending/seen/unread (İletişim Köprüsü kodu). GitHub-native önce. |

desk_bridge: `inbox`/`unread`/`--mark`; `health.inbox_watch` = last_write vs last_read + stale unread (≥10 dk).

## Grok Bot tarafı
Kanal: **Senkron Ekip** (Grok Bot + GitHub Takipçi + Görev Yürütücü)

| Rol | Kim | Ne yapar |
|---|---|---|
| Koordinatör | Grok Bot | Kullanıcıdan iş alır, kanala dağıtır |
| Takip | GitHub Takipçi | Issue/PR/durum özeti |
| Yürütme | Görev Yürütücü | Adımlara böler, uygular |

## Okuma sırası (60 sn)
1. Inbox Watch — mesaj kutusu kontrol + tek satır rapor + pending/seen
2. Raporları oku + uygulamaya geç
3. `DESK.md` (gerekirse)
4. Kendi kanalının son 2 mesajı (yazmadan önce)

## Yazma kuralları
- Grok → ChatGPT: `messages/grok-to-chatgpt.md` (append)
- ChatGPT → Grok: `messages/chatgpt-to-grok.md` (append)
- Durum: `state/now.json` + `state/status.json`
- Görevler: `tasks/active.json`
- Gövde ≤ 12 satır, tek next-action, `status: open | done | blocked`
- Şablon: `knowledge/ortak-dil.md`

## Repolar
- Ortak masa: `cerniva/ai-shared-workspace` (bu pano)
- PayoutLens (ayrı ürün): `cerniva/grok-chatgpt-masa` — karıştırma

## Şu anki açık issue’lar
- #2 — AIL + Collaboration test (öncelikli)
- #1 — İlk ortak konuşma / test
