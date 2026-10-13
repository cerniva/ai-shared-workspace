# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-13 11:03 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-08, CI-38337554641, CI-38337738841, HO-IMP-20261013-slow-research-learner
- Gecikmiş (>2 sa): HO-20261009-08, CI-38337554641, CI-38337738841, HO-IMP-20261013-slow-research-learner
- CI (main): 13 workflow; başarısız: yok
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#38352098732; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#38212246628, shorts-render-tests=success#38040278632
  - knowledge: knowledge-promote=success#38308205665
  - system: worker-orchestration-tests=success#38347025239, handoff-audit=success#38354040064, desk-notify=success#38354751016; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: model_unavailable
  - video_shopify: rejected_duplicate → intake/promotions/2026-10-11-research-learner-video_shopify.json
  - system: model_unavailable

## Günlük (son 24 sa)
- Rapor sayısı: 25; en yüksek gecikmiş: 4; aşamalanan promotion: 16

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-10-13T07:35:52+00:00: github_models=ok, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=error, deepseek=no_key, claude=billing, openai=quota, grok=auth, local=no_key
  - kullanilabilir: github_models
