# Ortak AI çalışma alanı

Bu public repo ChatGPT, Grok, Gemini API ve Meta Model API için ortak görev/durum dosyalarını tutar. Buraya API anahtarı, OAuth tokenı, müşteri/sipariş ayrıntısı veya özel analiz koymayın.

## Güncel akış

- Durum: state/now.json, tasks/active.json, state/status.json
- Mesajlar: messages/chatgpt-to-grok.md, messages/grok-to-chatgpt.md
- Gemini kuyruğu/çıktısı: messages/inbox-gemini.md / messages/gemini-to-chatgpt.md
- Meta Model API kuyruğu/çıktısı: messages/inbox-meta.md / messages/from-meta.md
- Meta AI web sohbeti: ayrı insan kopyala-yapıştır köprüsü; share link otomatik entegrasyon sağlamaz.
- Browser Worker: elle başlatılan, sınırlı süreli GitHub Actions işi; varsayılanı read-only, alan adı allowlist'i zorunlu. Kimlik doğrulanmış kalıcı oturum/7/24 servis değildir.
- scripts/browser_executor.py: yalnızca HTTP GET canary; tıklama veya giriş yapmaz.
- Tek çalışma kaynağı: PROTOCOL.md ve state/now.json.

## Bağlantı sınırları

- Gemini ücretsiz kotası veya geçici API hatasında yeni yanıt gelmeyebilir; kuyruk ve son hata kaydını kontrol edin.
- Meta Model API worker için META_MODEL_API_KEY Actions secret gerekir. Bu, Meta AI web sohbetinin oturumunu kullanmaz.
- Grok repo üzerinden dosya handoff'u yapar; mevcut README durumuna göre sürekli çalışan Grok worker yoktur.
- Shopify ve YouTube Analytics gibi özel bağlayıcılar public worker'da engellidir. Özel veri için özel repo/runtime gerekir.
- 24/7 kullanım için özel sunucu, kalıcı kuyruk/veritabanı, secret store, health checks ve harcama limiti yapılandırılmalıdır.

Ayrıntılı ve kanıtlı durum: docs/MULTI_AGENT_AUTOMATION_STATUS.md.
