# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-21 19:17 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527, HO-IMP-20261021-slow-auto-merge-gate, CI-39568642118, CI-39592612716, CI-39617972568
- Gecikmiş (>2 sa): HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527, HO-IMP-20261021-slow-auto-merge-gate, CI-39568642118, CI-39592612716
- CI (main): 14 workflow; başarısız: yok
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#39603165352; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#39210863552, shorts-render-tests=success#39214193921
  - knowledge: knowledge-promote=success#39009061465
  - system: worker-orchestration-tests=success#39603176328, handoff-audit=success#39615440240, desk-notify=success#39617972552; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: model_unavailable
  - video_shopify: model_unavailable
  - system: model_unavailable

## Günlük (son 24 sa)
- Rapor sayısı: 25; en yüksek gecikmiş: 8; aşamalanan promotion: 0

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-10-21T15:44:32+00:00: github_models=error, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=error, deepseek=no_key, claude=billing, openai=quota, grok=auth, local=no_key
  - kullanilabilir: YOK
