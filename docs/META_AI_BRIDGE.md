# Meta AI — insan köprüsü (masa el/ayak)

Tarih: 2026-09-26
Rol: web elleri / ayakları. Dördüncü beyin değil. Canlı model sohbeti yok; file-desk.

## Ne bu, ne değil

- Bu kanal: kullanıcının Meta AI sohbeti (Muse Spark / Glimmer UI).
- `docs/META_WORKER.md`: ayrı, henüz anahtarsız Model API worker taslağı. İkisi karıştırılmaz.
- Meta GitHub'a kendi yazamaz. Taşıma Furkan.

## Dosyalar

| Dosya | İş |
|---|---|
| `messages/inbox-meta.md` | Grok/ChatGPT → Meta görev kuyruğu |
| `messages/paste-from-meta.md` | Furkan yapıştırma kutusu |
| `messages/meta-to-chatgpt.md` | Masa içi özet kanalı |

## Kapılar

Yasak (insan onayı + ayrı private yol olmadan): login, OAuth, ödeme, yayın, silme, PayoutLens, secret yazma.

İzinli: herkese açık sayfa okuma, taslak form, ekran kanıtı, araştırma sentezi.

## Glimmer notu

Muse Glimmer açık ağırlık (Apache 2.0), lokal çalışır; Model API üzerinden çağrılmaz. Masa köprüsü şimdilik sohbet + yapıştırma. Lokal Glimmer kurulumu ayrı iş.
