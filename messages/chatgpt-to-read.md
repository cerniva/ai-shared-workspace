# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-22 11:22 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527, HO-IMP-20261021-slow-auto-merge-gate, CI-39568642118, CI-39592612716, CI-39617972568, HO-IMP-20261022-slow-shorts-render-tests, CI-39733548992
- Gecikmiş (>2 sa): HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527, HO-IMP-20261021-slow-auto-merge-gate, CI-39568642118, CI-39592612716, CI-39617972568, HO-IMP-20261022-slow-shorts-render-tests
- CI (main): 14 workflow; başarısız: yok
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#39729744941; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#39210863552, shorts-render-tests=success#39214193921
  - knowledge: knowledge-promote=success#39009061465
  - system: worker-orchestration-tests=success#39723843213, handoff-audit=success#39732418530, desk-notify=success#39733599383; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: model_unavailable
  - video_shopify: staged → intake/promotions/2026-10-22-research-learner-video_shopify.json
  - system: model_unavailable

## Günlük (son 24 sa)
- Rapor sayısı: 24; en yüksek gecikmiş: 10; aşamalanan promotion: 3

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-10-22T07:51:30+00:00: github_models=error, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=ok, deepseek=no_key, claude=billing, openai=quota, grok=auth, local=no_key
  - kullanilabilir: gemini
