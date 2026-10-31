# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-31 16:54 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527, HO-IMP-20261021-slow-auto-merge-gate, CI-39568642118, CI-39592612716, CI-39617972568, HO-IMP-20261022-slow-shorts-render-tests, CI-39733548992, CI-39755405014, HO-IMP-20261023-slow-archive-heal, HO-IMP-20261024-slow-worker-orchestration-tests, CI-40086311263, CI-40115771434, HO-IMP-20261025-slow-codeql-code-scanning, HO-IMP-20261027-slow-research-learner, HO-IMP-20261028-provider-cerebras, HO-IMP-20261029-slow-improvement-bot, HO-IMP-20261030-fail-shorts-cdc-source-audit, HO-IMP-20261031-slow-worker-orchestration-tests
- Gecikmiş (>2 sa): HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527, HO-IMP-20261021-slow-auto-merge-gate, CI-39568642118, CI-39592612716, CI-39617972568, HO-IMP-20261022-slow-shorts-render-tests, CI-39733548992, CI-39755405014, HO-IMP-20261023-slow-archive-heal, HO-IMP-20261024-slow-worker-orchestration-tests, CI-40086311263, CI-40115771434, HO-IMP-20261025-slow-codeql-code-scanning, HO-IMP-20261027-slow-research-learner, HO-IMP-20261028-provider-cerebras, HO-IMP-20261029-slow-improvement-bot, HO-IMP-20261030-fail-shorts-cdc-source-audit, HO-IMP-20261031-slow-worker-orchestration-tests
- CI (main): 15 workflow; başarısız: takipci-denetci
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#41194766998; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#40280828836, shorts-render-tests=success#40326197396
  - knowledge: knowledge-promote=success#41175737010
  - system: worker-orchestration-tests=success#41173462957, handoff-audit=success#41190739750, desk-notify=success#41186738151; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: already_in_ledger
  - video_shopify: staged → intake/promotions/2026-10-31-research-learner-video_shopify.json
  - system: already_in_ledger

## Günlük (son 24 sa)
- Rapor sayısı: 5; en yüksek gecikmiş: 22; aşamalanan promotion: 13

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-10-31T11:01:10+00:00: github_models=error, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=error, deepseek=no_key, claude=auth, openai=quota, grok=auth, local=no_key
  - kullanilabilir: YOK
