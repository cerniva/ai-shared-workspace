# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-19 09:15 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once
- Gecikmiş (>2 sa): HO-20261009-08
- CI (main): 14 workflow; başarısız: yok
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#39191113701; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#38212246628, shorts-render-tests=success#39185622154
  - knowledge: knowledge-promote=success#39009061465
  - system: worker-orchestration-tests=success#39191118650, handoff-audit=success#39198517288, desk-notify=success#39199704130; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: model_unavailable
  - video_shopify: already_in_ledger
  - system: model_unavailable

## Günlük (son 24 sa)
- Rapor sayısı: 24; en yüksek gecikmiş: 5; aşamalanan promotion: 0

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-10-19T05:53:59+00:00: github_models=error, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=quota, deepseek=no_key, claude=billing, openai=quota, grok=auth, local=no_key
  - kullanilabilir: YOK
