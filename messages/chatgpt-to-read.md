# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-10 23:52 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-03, HO-20261009-08, HO-IMP-20261010-slow-github-actions-in-update-1620214326
- Gecikmiş (>2 sa): HO-20261009-08, HO-IMP-20261010-slow-github-actions-in-update-1620214326
- CI (main): 7 workflow; başarısız: yok
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#38076121572; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#37991566901, shorts-render-tests=success#38040278632
  - knowledge: knowledge-promote=success#38040278599
  - system: worker-orchestration-tests=success#38076125449, handoff-audit=success#38081495753, desk-notify=success#38082064265; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: staged → intake/promotions/2026-10-09-research-learner-finance.json
  - video_shopify: staged → intake/promotions/2026-10-09-research-learner-video_shopify.json
  - system: model_unavailable

## Günlük (son 24 sa)
- Rapor sayısı: 24; en yüksek gecikmiş: 2; aşamalanan promotion: 46

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-10-10T20:26:57+00:00: github_models=ok, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=ok, deepseek=no_key, claude=billing, openai=quota, grok=auth, local=no_key
  - kullanilabilir: github_models, gemini
