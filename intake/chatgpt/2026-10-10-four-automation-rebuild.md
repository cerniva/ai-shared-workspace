# Furkan — dört otomasyonun yeniden kurulması (2026-10-10)

Yetki: Kullanıcı tüm otomasyonları ChatGPT+Grok işbirliğiyle sıfırdan çalışır hâle getirmeyi istedi. Mevcut öğrenmeler, kaynaklar, state, geçmiş ve çalışan kod korunur; PayoutLens kapsam dışıdır. "Sıfırdan" mevcut state'i silmek anlamına gelmez.

## Kabul kapıları (her plan için)
1. Gerçek tetikleyici: cron/workflow_dispatch ve/veya platform görevi; UTC/TRT saat dönüşümü kayıtlı. Schedule dosyası varlığı tek başına aktif çalışma kanıtı değildir.
2. Kaynak: erişim, kimlik, kota, tarih, veri kalitesi kontrolü; secret ve ödeme gerektiren aşamalar açıkça blocked_user.
3. Öğrenme: plan_learnings --require çalışır; runner JSON içindeki gerçek karar/learning_id'leri kullanır; applied_learning_ids manifest + read-back; göstermelik yükleme başarısız sayılır.
4. Çıktı: artifact, state ve messages kanalına kanıtlı rapor; e-posta teslimi ayrıca message_id/sent kanıtı ister.
5. Test: birim + entegrasyon + smoke + gerçek workflow run_id + main read-back; hatalı durumda otomatik düzeltme güvenli sınırda, 401/403/2FA sonsuz retry yok.
6. Bir sonraki tur: önceki state ve öğrenmeleri gerçekten okur, yeni kaynak/ders kaydeder; canonical dedup, atomik yayın, no secret/PII.
7. İdempotent ve düşük maliyetli: çift yayın/çift ürün/tekrarlı paid call yok; fail-closed ve rollback.

## Dört çalışma hattı
FINANS: primary sources -> timestamp -> macro/crypto/metals/energy/stocks/rates/FX -> verify -> altseason 10 indicators (missing historical calibration N/A) -> SVG chart gate where valid -> report -> calendar release alerts -> ledger.
VIDEO_SHOPIFY: research -> select -> 30s hook/storyboard -> rights -> original moving video/voice -> full MP4 QA -> channel OAuth check -> upload only if authorized -> Studio metrics -> next learnings; Shopify read-only product/landed-cost/margin/risk analysis -> draft, no irreversible actions without permission. Gumroad draft-first subflow.
BILGI_KUTUPHANESI: source discovery -> canonical separate source IDs -> verify availability -> learn -> stage promotions schema_version 1 -> all-or-nothing promote -> plan application -> read-back. Missing historical sources remain unverified.
SISTEM: inbox/fallback ack -> tasks/handoffs -> claim -> root cause -> small fix -> tests -> CI -> main read-back -> status and next task. Distinguish GitHub scheduled workflows from ChatGPT platform scheduled tasks; no invented cross-system trigger.

## Öncelikli eksikler / iş paylaşımı
ChatGPT: scope/acceptance audit, primary source/learning specifications, test evidence review, reporting.
Grok: inventory actual workflows, safe trigger wiring, runner fixes, integration and smoke tests, main merge and read-back; write SHA and run IDs to messages/grok-to-chatgpt.md.
P0: actual running schedules and outputs; HO-11 shorts applied_learning_ids main verify; finance/system runner absent in repo; YouTube OAuth upload blocked; no claims of delivery without run.
P1: 2020-25 altseason coverage/calibration, Shopify fields/scopes, Gumroad draft; no fictional green.
P2: cost, performance, monitoring, dedup, resilience.
Required evidence table per plan: trigger, runner, last run_id+timestamp, CI SHA, produced artifact, applied_learning_ids, delivery evidence, blockers, owner, next safe step.
Manual user action only when actual login/OAuth/2FA/payment required.

## Execution
Grok should read this file, reply with inventory+first minimal tested implementation; then proceed across all four plans without waiting for a new user message, but only to extent an actual autonomous workflow has been deployed. ChatGPT cannot truthfully promise continuous background execution from this chat alone.
