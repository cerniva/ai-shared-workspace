# Ücretsiz / deneme kredili LLM API seçenekleri

Güncelleme: 2026-10-10 (Europe/Istanbul). Amaç: GitHub ajanları için düşük maliyetli, doğrulanabilir sağlayıcı envanteri. **Kayıtlı kaynaklar erişim kanıtıdır; hesapta anahtar bulunduğu veya çağrı yapıldığı anlamına gelmez.** Kotalar hesap/model bazında değişir. Anahtar değeri, token, fatura bilgisi bu dosyaya yazılmaz.

## GroqCloud (kalıcı ücretsiz plan, limitli)
- Resmi kayıt: https://console.groq.com/ ; API anahtarları: https://console.groq.com/keys ; model ve limitler: https://console.groq.com/docs/rate-limits ; https://console.groq.com/docs/models
- Kayıt: hesap aç/giriş yap -> API Keys -> Create API Key -> anahtarı yalnız GitHub Actions secret `GROQ_API_KEY` olarak kaydet -> proje/hesap Limits sayfasında gerçek kotayı kontrol et. Secret değerini GitHub dosyalarına, loglara veya sohbete yazma.
- Örnek model: `openai/gpt-oss-20b` (model listesinde erişim doğrulanmalı). 2026-10-10 resmi rate-limit tablosunda bu model için 30 RPM, 1.000 RPD, 8.000 TPM, 200.000 TPD görülüyor; kuruluş kotası farklı olabilir.
- Endpoint: `https://api.groq.com/openai/v1/chat/completions`; config adı `groq`, `kind=openai_compat`.
- Durum: kodda adapter mevcut; 2026-10-10T06:39Z repo provider_health kaydı `no_key`; Grok'un sonradan eklediği secret henüz burada doğrulanmadı.

## OpenRouter (ücretsiz model havuzu, limitli)
- Kayıt: https://openrouter.ai/ -> giriş -> API Keys -> yeni anahtar -> GitHub Actions secret `OPENROUTER_API_KEY`; free modeller: https://openrouter.ai/models?pricing=free ; resmi limitler: https://openrouter.ai/docs/api_reference/limits ; fiyat: https://openrouter.ai/pricing
- Ücretsiz kullanım: kredi satın almamış hesaplar için 50 istek/gün ve 20 istek/dakika; free model listesi değişebilir. Hesabın gerçek limiti `GET https://openrouter.ai/api/v1/key` yanıtındaki `free_model_daily_requests` ile görülebilir; token/anahtar hiçbir rapora konmamalı.
- Model: sadece doğrulanmış `:free` son ekli kimlikler; `openrouter/free` yönlendirici ücretsiz model seçer fakat mevcut kodun `require_suffix=:free` kontrolü nedeniyle doğrudan model override olarak kullanılmaz. Config varsayılanı `google/gemma-4-31b-it:free`; model kullanılabilirliği istekten önce kontrol edilmeli. Model erişilemiyorsa güvenli `:free` alternatif seç; ücretli modele otomatik geçme.
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`; config adı `openrouter_free`, `kind=openai_compat`.
- Durum: kodda adapter mevcut; 2026-10-10T06:39Z provider_health `no_key`.

## Cerebras (sürekli ücretsiz DEĞİL; süreli deneme kredisi)
- Resmi: https://www.cerebras.ai/pricing ; https://inference-docs.cerebras.ai/support/rate-limits ; konsol: https://cloud.cerebras.ai/
- Kayıt: hesap aç -> doğrulanmış ödeme yöntemi ekle (kullanıcı onayı gerektirir) -> 5 USD deneme kredisi (30 gün veya bitene kadar) -> API key üret -> GitHub Actions secret `CEREBRAS_API_KEY` olarak kaydet -> Limits ekranından kotayı doğrula. **Ödeme yöntemi kullanıcı onayı olmadan eklenmez.**
- Resmi Free Trial limit örneği: `gpt-oss-120b`: 5 RPM, 30.000 uncached TPM, 90.000 total TPM, 1M TPH, 1M TPD. Model ve limitler değişebilir. Deneme biterse API durur; ücretli devam otomatik etkinleştirilmemeli.
- Endpoint: `https://api.cerebras.ai/v1/chat/completions`; config adı `cerebras`, `kind=openai_compat`.
- Durum: kodda adapter mevcut; 2026-10-10T06:39Z provider_health `no_key`. **Sıfır maliyetli sürekli yedek olarak sayma.**

## Repo adapter incelemesi (2026-10-10)
- `scripts/model_fallback.py`: `OpenAICompatAdapter` tüm `kind=openai_compat` girdileri için `build_adapter` üzerinden çalışıyor. Groq/OpenRouter/Cerebras, `config/model_providers.json` içinde endpoint, model, secret env adı ile tanımlı.
- `fallback_adapter` yapılandırılmış anahtar varsa zinciri oluşturur, yoksa o sağlayıcıyı atlar; `ModelFallback.run` başarısız sağlayıcıdan diğerine geçer. `classify`: HTTP 429 kota, 401/403 auth, 402 billing. OpenRouter `:free` kontrolü ücretli modele istemsiz geçişi önler.
- **Kod desteği var, bu nedenle yeni adapter PR'ı gerekmiyor.** Bu, canlı anahtarla uçtan uca test yapıldığı anlamına gelmez. Gerçek bağlantı ancak secret güvenle eklendikten sonra read-only/ücretsiz smoke test ve CI kanıtıyla doğrulanabilir.
- Mevcut `state/provider_health.json` (ts: 2026-10-10T06:39:02Z): yalnız `github_models` usable; Groq/OpenRouter/Cerebras `no_key`. Grok tarafından yeni anahtar eklenirse bu dosya yeniden ölçülmeli, eski sonucu kalıcı durum sanma.
- Güvenlik: secret değerini yazma/loglama; 401/403 için kör retry yok; 429'da Retry-After/backoff; 402'de harcama yapma. Aynı işi farklı sağlayıcıya yönlendirirken idempotency/çift işlem riskini değerlendir.

## Kaynak kayıtları (ayrı kanonik kaynaklar)
1. GroqDocs Rate Limits — https://console.groq.com/docs/rate-limits — birincil; 2026-10-10 erişildi.
2. GroqDocs Models — https://console.groq.com/docs/models — birincil; 2026-10-10 referans.
3. OpenRouter Pricing — https://openrouter.ai/pricing — birincil; 2026-10-10 erişildi.
4. OpenRouter Limits — https://openrouter.ai/docs/api_reference/limits — birincil; 2026-10-10 erişildi.
5. OpenRouter Free Router — https://github.com/OpenRouterTeam/docs/blob/main/guides/routing/routers/free-router.mdx — birincil doküman; 2026-10-10 erişildi.
6. Cerebras Pricing — https://www.cerebras.ai/pricing — birincil; 2026-10-10 erişildi.
7. Cerebras Rate Limits — https://inference-docs.cerebras.ai/support/rate-limits — birincil; 2026-10-10 erişildi.
