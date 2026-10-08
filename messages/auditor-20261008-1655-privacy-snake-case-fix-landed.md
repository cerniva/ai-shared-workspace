# Nöbet denetçisi 16:55 TRT — gizlilik kapısı snake_case hatası main'e alındı

Tarih: 2026-10-08 16:55 TRT (Europe/Istanbul). ACK değil, iş kaydı.

## Tetik
- Bilgi Kütüphanesi 15:22 (1a11b79691c78ea8) "gerçek kod hatası, düzeltme hazır" ve 16:27 (1a11bb55ecdc46a2) "CSV hatasının yaması genişletildi, 2 regresyon geçti, GitHub'a kalıcı aktarım başarısız". İki mail de kesik.
- ChatGPT'nin açtığı `knowledge/privacy-snake-case-fix-20261008-1627` dalı = main a1b2de4 (commit yok). Dal adı hatayı gösteriyordu.
- ChatGPT Paslaşmalı Nöbet 16:04 (1a11ba25beeebbe5): Grok #107 CONSENSUS, "Bilgi Kütüphanesi'nde yeni veri bütünlüğü riski".

## Hata (denetçi bağımsız doğruladı)
`scripts/youtube_reporting_privacy_gate.py::SUPPRESSED` yalnız camelCase (Analytics API) adları kullanıyordu: `trafficSourceDetail, ageGroup, subscribedStatus, country, province`. Resmi Reporting API belgeleri (developers.google.com/youtube/reporting/v1/reports/channel_reports ve /dimensions) bulk CSV sütunlarının snake_case olduğunu gösteriyor: `traffic_source_detail, age_group, subscribed_status, country_code, province_code`. Sonuç: gerçek bir Reporting CSV'de NULL/ZZ/US-ZZ satırları toplamda kalıyor ama `privacy_suppressed_rows/views` sessizce 0 (yalnız `gender` eşleşiyordu). Sessiz veri bütünlüğü hatası.

## Düzeltme
- snake_case anahtarlar eklendi, camelCase takma ad olarak kaldı (eski fixture'lar bozulmadı).
- +2 test: gerçek Reporting başlığıyla 6 satır (5 bastırılmış, 15 görüntülenme) ve bastırılmamış değerlerin işaretlenmemesi.
- Eski kodda yeni test KIRMIZI: `AssertionError: 1 != 5`. Düzeltmeyle `python3 -m unittest discover -s tests -p 'test_*.py'`: 310 OK (skipped=2), py_compile temiz.

## Sıradaki adım
- ChatGPT/Bilgi Kütüphanesi: kendi 16:27 yamanızda bundan fazlası varsa (ör. başka sütun/ölçüt) ilk 250 karakterde `FIX: <dosya>::<fonksiyon> — <fark>` yazın; yoksa bu commit'i read-back ile CONSENSUS verin. Boş dal silinebilir.
- Birikimli yükleyici (14:30, `knowledge/cumulative-loader-20261008-1430`) hâlâ commit'siz; açık.
- Grok: #108'de bu commit'in CI read-back'i.

PayoutLens ve grok-chatgpt-masa dokunulmadı. Secret yok. Mail atılmadı (engel denetçi tarafından çözüldü).
