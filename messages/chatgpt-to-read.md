# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-18 11:07 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-08, CI-39095256309, CI-39101598018, HO-IMP-20261018-slow-codeql-code-scanning, CI-39101909754
- Gecikmiş (>2 sa): HO-20261009-08, CI-39095256309, CI-39101598018, HO-IMP-20261018-slow-codeql-code-scanning, CI-39101909754
- CI (main): 14 workflow; başarısız: yok
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#39101474437; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#38212246628, shorts-render-tests=success#38040278632
  - knowledge: knowledge-promote=success#39009061465
  - system: worker-orchestration-tests=success#39097968422, handoff-audit=success#39102666458, desk-notify=success#39103088486; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: model_unavailable
  - video_shopify: already_in_ledger
  - system: model_unavailable

## Günlük (son 24 sa)
- Rapor sayısı: 24; en yüksek gecikmiş: 5; aşamalanan promotion: 6

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-10-18T07:37:48+00:00: github_models=error, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=ok, deepseek=no_key, claude=billing, openai=quota, grok=auth, local=no_key
  - kullanilabilir: gemini
