# Ajan raporu (GitHub-hosted ajanlar) — ChatGPT önce bunu okur

Zaman: 2026-10-10 02:57 TRT

## Saatlik
- Açık/claimed handoff: HO-20261009-03, HO-20261009-08, HO-20261010-12, HO-20261010-13
- Gecikmiş (>2 sa): HO-20261009-08
- CI (main): 14 workflow; başarısız: yok
- Otomasyonlar (automation-runner):
  - finance: plan-learnings-check=success#37999890427; tetiklenen: plan-learnings-check.yml
  - video_shorts_shopify_gumroad: shorts-free-build=success#37995367680, shorts-free-render=never_run, youtube-upload=failure#36506246392, tinyfish-youtube-analytics=success#37991566901, shorts-render-tests=success#37999563352
  - knowledge: knowledge-promote=success#37999870563
  - system: worker-orchestration-tests=success#38000057827, handoff-audit=success#38000057820, desk-notify=success#38000009735; tetiklenen: worker-orchestration-tests.yml
- Araştırma (research-learner, inceleme için intake/promotions/):
  - finance: staged → intake/promotions/2026-10-09-research-learner-finance.json
  - video_shopify: staged → intake/promotions/2026-10-09-research-learner-video_shopify.json
  - system: model_unavailable

## Günlük (son 24 sa)
- Rapor sayısı: 3; en yüksek gecikmiş: 1; aşamalanan promotion: 4

Not: Ajanlar main'deki koda yazmaz; yalnız state/, messages/ ve intake/ altına yazar. Yayın/upload/ödeme workflow'ları yalnız gözlenir (dry-run).
