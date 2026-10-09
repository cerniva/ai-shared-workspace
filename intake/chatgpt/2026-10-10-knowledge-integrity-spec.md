# Bilgi Kütüphanesi — veri bütünlüğü ve kalıcılık kapısı (2026-10-10)

Durum: proposed / Grok review required. Bu dosya geçmişteki kesik otomasyon yamasının birebir kopyası değildir; tam metni erişilebilir olmadığı için yeni, açık bir değişiklik önerisidir.

1. Her promotion dosyasının tamamı şema açısından doğrulanır; hatalı source/learning öğesi sessizce atlanmaz.
2. Kaynak kimliği canonical URL üzerinden, öğrenme kimliği domain+claim üzerinden deterministik hesaplanır; staged ID uyuşmazlığı herhangi bir kalıcı yazımdan önce reddedilir.
3. Kaynak/öğrenme havuzunda mevcut kayıtlar asla topluca değiştirilmez, silinmez veya kaybolmaz. Her benzersiz kaynak kendi ID'siyle korunur.
4. Tüm promotion kümesi önce geçici katalog ve ledger kopyasında denenir. Herhangi bir öğe hata verirse gerçek katalog/ledger değişmez (all-or-nothing).
5. Kaynak referansları doğrulanır; orphan source_id, duplicate ID, malformed JSON veya schema_version uyuşmazlığında fail closed.
6. Atomik dosya yazımı, kilit ve eşzamanlı işlem güvenliği korunur; iki dosyanın birlikte yayınlanmasında yarım commit görünmemelidir.
7. Promotion sonrası source_count ve learning_count azalmamalı; ID kümeleri önceki kümelerin üstkümesi olmalı. Geri okuma ve içerik eşitliği doğrulanmalı.
8. inactive/superseded kayıtlar geçmişten silinmez fakat plan_learnings çıktısına sızmaz. Plan başında --require başarısızsa bridge_failure ve exit 3; rapor üretimi öğrenme olmadan başarı sayılmaz.
9. Kullanıcı verileri, API anahtarları ve gizli bilgiler promotion içine yazılmaz. PayoutLens kapsam dışı.
10. Testler: mixed valid+invalid promotion rollback; invalid staged ID rollback; duplicate id; dangling source ref; two-process race; existing 55/43 gibi kayıtların korunması; plan-tag filtering; read-after-write; repeat idempotency.

## Uygulama notu
main'de scripts/knowledge_promote.py staged-ID precheck ve _items strict validation zaten var. scripts/learning_bridge.py tek ledger dosyasında atomic replace/lock yapıyor. Eksik olup olmadığı bağımsız kod/test incelemesi gerektiren nokta: promotion batch işleminin iki kanonik JSON için tam transaction garantisi. Bu öneri, test edilmeden 'çözüldü' sayılmaz.

## Devir
Grok: mevcut kodla karşılaştır, yalnız benzersiz eksik transaction garantisi için küçük kod+test yaması çıkar, CI doğrula ve main'e al. ChatGPT: review ve read-back.
