# Grok Ops Bot (v1)

Amaç: Furkan + ChatGPT + Grok için işe yarayan bağlantıları tek botta toplamak.
Canlı model-model sohbet yok. SoT = GitHub file-desk.

## Ne yapar

1. Inbox oku (`messages/chatgpt-to-grok.md`, `state/now.json`).
2. Görevi sınıfla: observe | draft | apply_safe | approval_required.
3. API varsa API; yoksa tarayıcı yedek (allowlist).
4. Kanıtı `outputs/` + ilgili message kanalına yaz.
5. Para / yayın / silme / sipariş / OAuth → dur, Furkan onayı.

PayoutLens dokunulmaz.

## Bu sohbette Grok'ta şu an var

- GitHub (masa, kod, commit)
- Linear (iş takibi)
- Notion, Gmail, Vercel, Netlify, Figma, Canva, Gamma
- Wix, Whop
- Automations (zamanlanmış Grok işi)
- Voice, HyperFrames
- Web tarayıcı (observe)

## Bu sohbette yok / kritik açık

- Shopify connector (Grok chat) — ChatGPT tarafında var; Grok'ta yok
- Stripe (checkout / ödeme sağlığı)
- Google Drive (dosya / SOP ZIP)
- Google Calendar
- Buffer (içerik planı)

Worker secrets (public repo'ya yazılmaz): `SHOPIFY_STORE`, `SHOPIFY_CLIENT_ID`, `SHOPIFY_CLIENT_SECRET` — `docs/NEXT_CONNECTORS_SETUP.md`.

## İşe yarayan görev tipleri (v1)

| Görev | Araç | Onay |
|---|---|---|
| Katalog / taslak ürün analizi | ChatGPT Shopify snapshot veya Admin API read | yok |
| Repo / protokol / kuyruk | GitHub | yok |
| Görev aç | Linear | yok |
| Taslak içerik / SOP metin | Notion + Canva | yok |
| Vitrin açık mı | tarayıcı observe | yok |
| Ürün yayınla / fiyat değiştir | Shopify write | Furkan |
| Ödeme / sipariş / abonelik | Stripe / panele tıkla | Furkan |

## v1 teslim tanımı

Bot "yeni beyin" değil; mevcut worker + desk + bağlı araçlar üzerine ince katman:

- sınıf: observe/draft/apply_safe/approval_required (`docs/external-action-agent.md`)
- kuyruk: `scripts/work_queue.py`
- kanıt: tek next-action, blocker ayrı
- eksik bağlantı: ChatGPT'ye desk üzerinden delege; sırrı kullanıcıdan kopyalatma

## Şu anki somut blok

Storefront şifreli. 9 ürün DRAFT. Pet-hair fiyatı yayına hazır değil. SOP yanlış ZIP (TSK-009) ChatGPT lane.
