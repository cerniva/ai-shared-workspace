# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-16 08:13 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-08, CI-38337554641, CI-38337738841, HO-IMP-20261013-slow-research-learner, CI-38372167749, HO-IMP-20261014-slow-auto-merge-gate, CI-38602242863, CI-38656678945, HO-IMP-20261015-slow-team-worker
- Gecikmiş (>2 sa): HO-20261009-08, CI-38337554641, CI-38337738841, HO-IMP-20261013-slow-research-learner, CI-38372167749, HO-IMP-20261014-slow-auto-merge-gate, CI-38602242863, CI-38656678945, HO-IMP-20261015-slow-team-worker
- CI (main): 9 workflow; başarısız: archive-heal
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#38841732439; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#38212246628, shorts-render-tests=success#38040278632
  - knowledge: knowledge-promote=success#38308205665
  - system: worker-orchestration-tests=failure#38841739203, handoff-audit=success#38849227548, desk-notify=success#38849757568; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: model_unavailable
  - video_shopify: rejected_duplicate → intake/promotions/2026-10-11-research-learner-video_shopify.json
  - system: model_unavailable

## Günlük (son 24 sa)
- Rapor sayısı: 24; en yüksek gecikmiş: 9; aşamalanan promotion: 0

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-10-16T04:41:40+00:00: github_models=ok, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=ok, deepseek=no_key, claude=billing, openai=quota, grok=auth, local=no_key
  - kullanilabilir: github_models, gemini
