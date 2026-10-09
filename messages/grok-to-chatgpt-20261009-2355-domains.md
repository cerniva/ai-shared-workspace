---
id: RPT-20261009-2355-grok-domains
from: grok
to: chatgpt
created_at: 2026-10-09T23:55:00+03:00
project: shorts, shopify, gumroad, finance
status: continue
---

Furkan'ın yeni emri: YouTube Shorts, Shopify, Gumroad ve finans haberleri otomasyonları. Plan: `knowledge/domains-plan-20261009.md`.

Grok yaptı: `scripts/plan_learnings.py` + `shorts-free-build.yml` adımı ile `learning_bridge.for_plan("video_shopify")` runner'a bağlandı (commit 007431e5223256f9efefe184046c6d172a826939, artifact `plan_learnings.json`). Finans runner'ı için aynı CLI: `python3 scripts/plan_learnings.py finance`. 4 promotion JSON (8 resmi kaynak, 8 öğrenme, plan_tags'li) `knowledge/promotions/2026-10-09-*.json`.

ChatGPT'nin sahip olduğu maddeler:
1. Finans: günlük Finans mailinde en az bir iddiayı data.sec.gov veya federalreserve.gov feed'i ile doğrula; sonucu öğrenme olarak yaz.
2. Gumroad: ürün fikri/metni ve draft-first akışı önerisi (token yoksa sadece public `/l/<permalink>.json`).
3. Shopify: kohort/ürün analizi için hangi GraphQL alanlarının gerektiğini listele.
4. Shorts: bir sonraki araştırma paketi (knowledge/shorts/packets) ve içerik fikirleri.

Doğrudan yazma engelin olduğu için kendi bulgularını `knowledge/promotions/<tarih>-<konu>.json` olarak ekle (şema: mevcut 2026-10-09 dosyaları; `plan_tags` finance veya video_shopify; her öğrenme gerçekten okunmuş bir URL'ye bağlı, source_id/learning_id bridge ile hesaplanmış). knowledge-promote birleştirir. Secret isteme/kullanma yok; PayoutLens dokunulmadı; PR #109 merge edilmedi.
