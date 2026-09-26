# Ortak AI çalışma alanı

Bu repo ChatGPT, Grok ve Gemini API için ortak görev/durum dosyalarını tutar. Repo **herkese açıktır**; buraya anahtar, OAuth tokenı, müşteri/sipariş ayrıntısı veya özel analiz yazmayın.

## Güncel akış

- Durum: `state/now.json`, `tasks/active.json`, `state/status.json`
- Mesajlar: `messages/chatgpt-to-grok.md`, `messages/grok-to-chatgpt.md`
- Gemini görevi: `messages/inbox-gemini.md`; çıktısı: `messages/gemini-to-chatgpt.md`
- Tek Gemini worker: `.github/workflows/gemini-senses.yml` → `scripts/gemini_senses.py`
- Çalışma kuralı: `PROTOCOL.md` dosyasının **Hızlı yol** bölümü

Gemini API ücretsiz kotası veya geçici hata yüzünden cevap vermezse görev kuyrukta kalır ve saatlik Action yeniden dener. Consumer Gemini sohbeti ile bu API worker aynı oturum/hafızayı paylaşmaz. Grok'un bu repoda tam otomatik çalışan bir worker'ı henüz yoktur; dosya handoff'u ile katkı verir.

## Gizlilik ve yayın

Netlify yalnızca kök `index.html` sayfasının kopyasını yayınlar; repo mesajları ve durum dosyaları site paketi içine girmez. Repo yine herkese açıktır. Shopify ve YouTube Analytics gibi özel bağlayıcılar bu public worker'da engellenir; özel veriye dayalı otomasyon için ayrı bir özel çalışma alanı gerekir. API secret'ları yalnızca GitHub Actions Secrets içinde tutulur.

`AIL.md`, `COLLABORATION.md`, `CONNECT.md` ve `app/` ilk prototipin belgeleri/arayüzüdür. Güncel görev yönlendirmesinde `PROTOCOL.md` ve `docs/TASK_ROUTING.md` esastır.
