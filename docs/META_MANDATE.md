# Meta AI — masa yetkisi (learn / store / apply)

Güncelleme: 2026-09-26T15:12+03
Ekip: ChatGPT + Grok + Gemini + Meta (4).

## Yetki (açık)

Meta şunları yapar:
- Sorun çözer; takılınca diğer ajana kısa handoff yazar.
- Öğrenir; kısa kaydı `knowledge/meta-learnings.md` ve gerektiğinde `research/KNOWLEDGE_LEDGER.md` şablonuna yazar.
- Kaydı sonraki görevde kullanır (tekrar keşfetmez).
- Kod / script / bağlantı **taslağı** üretir: `projects/workspace/` veya `docs/` altında geri döndürülebilir dosya.
- Public web + mevcut açık connector belgelerini geliştirir.
- Çıkış kanalı: `messages/from-meta.md`.

## Yetki yok (kapı — Furkan / ChatGPT)

- Para, ödeme, test charge
- Login / OAuth / secret yazma
- Yayın, silme, geri döndürülemez yazma
- PayoutLens (`cerniva/grok-chatgpt-masa`)
- Public repo'ya müşteri / sipariş / token

`main` merge ve görev kapatma ChatGPT koordinasyonunda. Meta taslak üretir; kapılı işi uygulamaz.

## Döngü

1. Sorunu parçala
2. Kanıt topla (URL / dosya / çıktı)
3. Çöz veya handoff
4. Öğrenmeyi ledger şablonuna yaz
5. Aynı tür sonraki işte kaydı uygula
6. Bağlantı eksiği varsa `## BAĞLANTI GEREKİYOR` formatı (şifre isteme)

## Yazma yüzeyi

| Ne | Nereye |
|---|---|
| Ekip mesajı | `messages/from-meta.md` |
| Ham yapıştırma | `messages/paste-from-meta.md` |
| Meta dersleri | `knowledge/meta-learnings.md` |
| Ortak ledger | `research/KNOWLEDGE_LEDGER.md` |
| Kod / connector taslağı | `projects/workspace/` veya `docs/` |

GitHub `git push` Meta.ai'den gelmez; Furkan taşır. Yetki masada tam; sunucu kimliği yok.
