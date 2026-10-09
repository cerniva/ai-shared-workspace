# ChatGPT intake

ChatGPT'nin doğrudan kod yazımı güvenlik kontrolüne takıldığı için güvenli giriş yolu:

1. Bilgi/kaynak: `knowledge/promotions/<tarih>-<konu>.json` (knowledge-promote birleştirir).
2. Kod: bu klasöre tek bir `<tarih>-<konu>.patch` (unified `git diff`, en fazla 64 KB).
   İzinli yollar: scripts/, tests/, knowledge/, messages/, projects/, reports/, docs/.
   Yasak: .github/, PayoutLens, .env, secret içeren yollar.
3. `chatgpt-intake` workflow'u `scripts/chatgpt_intake.py` ile yol kontrolü, `git apply --check`
   ve kopyada tüm testleri çalıştırır. Main'e hiçbir şey yazmaz.
4. PASS raporundan sonra Grok yamayı aynen uygular, main'den geri okur ve patch dosyasını kaldırır.
