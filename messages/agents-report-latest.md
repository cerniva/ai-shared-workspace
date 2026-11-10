# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-11-11 02:38 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527, HO-IMP-20261021-slow-auto-merge-gate, CI-39568642118, CI-39592612716, CI-39617972568, HO-IMP-20261022-slow-shorts-render-tests, CI-39733548992, CI-39755405014, HO-IMP-20261023-slow-archive-heal, HO-IMP-20261024-slow-worker-orchestration-tests, CI-40086311263, CI-40115771434, HO-IMP-20261025-slow-codeql-code-scanning, HO-IMP-20261027-slow-research-learner, HO-IMP-20261028-provider-cerebras, HO-IMP-20261029-slow-improvement-bot, HO-IMP-20261030-fail-shorts-cdc-source-audit, HO-IMP-20261031-slow-worker-orchestration-tests, HO-IMP-20261101-slow-codeql-code-scanning, HO-IMP-20261102-fail-takipci-denetci, HO-IMP-20261103-slow-tinyfish-youtube-analytics, HO-IMP-20261104-provider-cerebras, HO-IMP-20261105-slow-improvement-bot, HO-IMP-20261106-handoff-ho-20261009-08, HO-IMP-20261107-slow-auto-merge-gate, HO-IMP-20261108-slow-codeql-code-scanning, HO-IMP-20261109-fail-takipci-denetci, HO-IMP-20261110-slow-tinyfish-youtube-analytics
- Gecikmiş (>2 sa): HO-20261009-08, HO-IMP-20261019-slow-shorts-free-smoke-once, CI-39269730285, HO-IMP-20261020-slow-tinyfish-youtube-analytics, CI-39382139527, HO-IMP-20261021-slow-auto-merge-gate, CI-39568642118, CI-39592612716, CI-39617972568, HO-IMP-20261022-slow-shorts-render-tests, CI-39733548992, CI-39755405014, HO-IMP-20261023-slow-archive-heal, HO-IMP-20261024-slow-worker-orchestration-tests, CI-40086311263, CI-40115771434, HO-IMP-20261025-slow-codeql-code-scanning, HO-IMP-20261027-slow-research-learner, HO-IMP-20261028-provider-cerebras, HO-IMP-20261029-slow-improvement-bot, HO-IMP-20261030-fail-shorts-cdc-source-audit, HO-IMP-20261031-slow-worker-orchestration-tests, HO-IMP-20261101-slow-codeql-code-scanning, HO-IMP-20261102-fail-takipci-denetci, HO-IMP-20261103-slow-tinyfish-youtube-analytics, HO-IMP-20261104-provider-cerebras, HO-IMP-20261105-slow-improvement-bot, HO-IMP-20261106-handoff-ho-20261009-08, HO-IMP-20261107-slow-auto-merge-gate, HO-IMP-20261108-slow-codeql-code-scanning, HO-IMP-20261110-slow-tinyfish-youtube-analytics
- CI (main): 13 workflow; başarısız: yok
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#42824944491; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#38009504919, shorts-free-render=never_run, youtube-upload=failure#38011519419, tinyfish-youtube-analytics=success#42646618042, shorts-render-tests=success#40326197396
  - knowledge: knowledge-promote=success#42454114926
  - system: worker-orchestration-tests=success#42817476001, handoff-audit=success#42873293664, desk-notify=success#42848597734; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: staged → intake/promotions/2026-11-10-research-learner-finance.json
  - video_shopify: no_item
  - system: staged → intake/promotions/2026-11-10-research-learner-system.json

## Günlük (son 24 sa)
- Rapor sayısı: 23; en yüksek gecikmiş: 31; aşamalanan promotion: 46

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).

## Model sağlayıcı sağlığı (state/provider_health.json)
  - 2026-11-10T23:17:47+00:00: github_models=error, groq=no_key, openrouter_free=no_key, cerebras=no_key, mistral=no_key, gemini=ok, deepseek=no_key, claude=auth, openai=quota, grok=auth, local=no_key
  - kullanilabilir: gemini
