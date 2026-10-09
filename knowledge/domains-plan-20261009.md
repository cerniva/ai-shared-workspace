# Alan planı — 2026-10-09 (Shorts, Shopify, Gumroad, Finans haberleri)

Kaynak: cerniva/ai-shared-workspace main, Grok envanteri 23:55 TRT. PayoutLens kapsam dışı. PR #109 merge edilmedi.

## Ortak düzeltme
- `scripts/plan_learnings.py` (`LearningLedger.for_plan` sarmalayıcı, yalnız aktif ve plan etiketli satırlar; ledger bozuksa runner durmaz, `error` dolar). `shorts-free-build.yml` render öncesi `plan_learnings.py video_shopify` çalıştırıp `artifacts/plan_learnings.json`u artifact olarak yüklüyor. Test: `tests/test_plan_learnings.py`. SHA: 007431e5223256f9efefe184046c6d172a826939.
- 4bbc3b34a9401e00a7a25c56fd276f837220d4df: `for_plan` inactive/superseded/replaced satırları dışlar; `plan_learnings.py --require` + `plan-learnings-check` (finance/video_shopify/system); `intake/chatgpt/*.patch` doğrulayıcı; `scripts/handoff.py` + `state/handoffs.json`.
- Promotion commit 0bc915cf81af24b18e8b0b8847570fa3fb0057c4, knowledge-promote birleştirmesi dbbf933 (main'de finance 2, video_shopify 7, system 1).
- Yeni promotion JSON: `knowledge/promotions/2026-10-09-*.json` (8 kaynak, 8 öğrenme, hepsi `plan_tags` ile). knowledge-promote birleştirince `for_plan` sayısı finance 0→2, video_shopify 1→7 olur.

| Alan | Durum | Sorun | Yapılan düzeltme | Alternatif yol | Sahip | Sonraki adım |
|---|---|---|---|---|---|---|
| YouTube Shorts | Kod + testler var (shorts-free-build/render/smoke, youtube-upload). Sadece workflow_dispatch; shorts-free-build hiç çalışmamış, youtube-upload son 2 koşu 29 Eylül push hatası. | Gerçek yükleme için YOUTUBE_CLIENT_ID/SECRET/REFRESH_TOKEN, medya için PEXELS/PIXABAY anahtarı gerekiyor (yalnız Furkan). privacyStatus açık gönderilmezse varsayılan public. | for_plan shorts-free-build runner'ına bağlandı (007431e5223256f9efefe184046c6d172a826939); kota/privacy öğrenmeleri eklendi. | Anahtar yoksa yerel/lisanslı medya ile render + artifact; upload dry-run. | Grok (kod), ChatGPT (içerik paketi) | Furkan secret'ları eklerse shorts-free-smoke-once tek koşu; upload'da privacyStatus=private zorunlu kapısı. |
| Shopify | `scripts/connectors/shopify_client.py`, retention_shopify_validation, shopify_worker testleri. Workflow yok. | SHOPIFY_STORE/CLIENT_ID/CLIENT_SECRET yok (yalnız Furkan). GraphQL hatası HTTP 200 ile gelir. | 2 öğrenme: leaky bucket/250/25k sınırları, 200-hata kapısı. | Admin CSV export ile manuel veri (user_reported). | Grok (client kapıları), ChatGPT (ürün/kohort analizi) | shopify_client'a errors[].extensions.code sınıflandırma testi. |
| Gumroad | Repoda hiçbir şey yok (kod, workflow, mail yok). | Hesap/ürün/token bilinmiyor. | 2 öğrenme: draft-first, files tam değiştirme, public .json izleme. | Token olmadan public `/l/<permalink>.json` ile salt-okur izleme. | ChatGPT (ürün fikri/metin), Grok (izleyici script) | Furkan bir ürün permalink'i verirse günlük fiyat/puan anlık görüntüsü. |
| Finans haberleri | Saatlik ChatGPT "[Task Update] Finans" mailleri (6–9 Ekim), `projects/finance/tcmb_fx.py`, `knowledge/finance_runtime_state.json`. | Mail önizlemeleri kesik; ikincil kaynaklara (Investing.com bülteni) dayanma; finans için plan etiketli öğrenme 0'dı. | 2 öğrenme: SEC EDGAR keysiz API + 10 req/s, Fed RSS. | EDGAR Latest Filings RSS, federalreserve.gov newsevents. | ChatGPT (günlük mail), Grok (kaynak doğrulama) | Bir sonraki Finans mailinde 1 iddiayı data.sec.gov/Fed feed ile doğrula. |

## Yalnız Furkan'ın açabileceği
YouTube OAuth secret'ları, Pexels/Pixabay anahtarları, Shopify mağaza kimlik bilgileri, Gumroad hesabı/token'ı ve ürün listesi. Ajanlar secret istemez/kullanmaz.
