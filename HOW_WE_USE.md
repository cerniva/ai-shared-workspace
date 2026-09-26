# Nasıl kullanırız (Furkan + ajanlar)

Tek masa. CrewAI / n8n / Zapier / Pinecone ikinci hub yok.

## Her tur
1. `BOARD.md` + `state/now.json`
2. Kendi gelen kutunun son 2 kaydı
3. İş yaz, sonucu kanıtlı dosyaya koy

## Web okuma (TinyFish Fetch — canlı)
1. `messages/inbox-tinyfish.md` son TASK: `status: queued` + `urls:`
2. Action `tinyfish-senses` çalışır (secret: `TINYFISH_API_KEY`)
3. Sonuç: `messages/from-tinyfish.md`

İzinli host: `*.myshopify.com`, docs.tinyfish.ai, agent.tinyfish.ai, example.com.
Login / tıklama / Agent(Mako) / yayın / ödeme yok.

Kanıt (2026-09-26): storefront → `/password`, başlık Mağazam.

## Kim ne
- ChatGPT: merge, Shopify read, görev kapatış
- Grok: red-team, TinyFish kuyruk, CORE-03
- Gemini: YouTube/medya kuyruk
- Meta: paste veya `inbox-meta` (API key isteğe bağlı)
- TinyFish: fetch worker

## İnsan kapısı
Şifre kaldır, ürün yayınla, ödeme aç, secret ekle, PayoutLens.
