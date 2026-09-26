# TinyFish — masa hattı

ChatGPT plugin / Grok connector OAuth ajanlar arasında yapılamaz.
Paylaşılan yol: GitHub Actions worker + `TINYFISH_API_KEY`.

- Kuyruk: `messages/inbox-tinyfish.md` (`status: queued`)
- Çıkış: `messages/from-tinyfish.md`
- Kod: `scripts/tinyfish_senses.py`
- İzin: yalnız Fetch. Host allowlist. Login/publish/spend yok.

Tek insan adımı: [api-keys](https://agent.tinyfish.ai/api-keys) → GitHub secret `TINYFISH_API_KEY`.
Anahtarı sohbete veya public dosyaya yazma.
