# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-21 06:15 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527
- Gecikmiş (>2 sa): HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527
- CI (main): 16 workflow; başarısız: yok
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#39524087882; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#39210863552, shorts-render-tests=success#39214193921
  - knowledge: knowledge-promote=success#39009061465
  - system: worker-orchestration-tests=failure#39524096109, handoff-audit=success#39531588990, desk-notify=success#39532037157; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: model_unavailable
  - video_shopify: already_in_ledger
  - system: model_unavailable

## Günlük (son 24 sa)
- Rapor sayısı: 24; en yüksek gecikmiş: 5; aşamalanan promotion: 0

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-10-21T02:40:24+00:00: github_models=error, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=ok, deepseek=no_key, claude=billing, openai=quota, grok=auth, local=no_key
  - kullanilabilir: gemini
