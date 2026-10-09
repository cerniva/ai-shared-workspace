# Birleşik Video, Shorts, Shopify ve Gumroad otomasyonu

Furkan talimatı: Gumroad, Video/Shorts/Shopify ana otomasyonuna eklenir; dört ana otomasyon sayısı değişmez. Mevcut kaynaklar ve öğrenmeler korunur. PayoutLens kapsam dışı.

## Ortak döngü

Araştırma -> fırsat seçimi -> özgün içerik veya ürün taslağı -> lisans, kalite, maliyet doğrulama -> yetkili yayın -> analitik -> yeni öğrenme -> sonraki turda uygulama. video_shopify etiketi geriye uyumlu kalır; Gumroad öğrenmeleri de aynı planda okunur. applied_learning_ids gerçekten uygulanan kararları yansıtmalı.

## Shorts

30 saniye, 9:16 hareketli özgün video, hook/storyboard, ses, lisans, MP4 tam süre kalite testi. OAuth ve hedef kanal doğrulanmadan yükleme yok. Engaged views, retention ve abonelik etkisi ölçülür.

## Shopify

Talep, landed cost, marj, kargo, kalite, iade ve haklar analizi. Gerçek GraphQL izinleri doğrulanmadan canlı mağaza değişikliği yok. Taslak öncelikli.

## Gumroad

Orijinal dijital ürünler: ilk aday Mutfağın Hammaddeleri kitabı. Tamamlanmamış içerik satılmaz. Dosya, kapak, açıklama, fiyat/komisyon ve teslim testi; taslak öncelikli. Hesap bağlantısı ve izin doğrulanmadan yayın, satış ayarı veya ödeme değişikliği yok. Erişim yoksa yerel taslak üret ve engeli raporla.

## Grok uygulama ve kabul

Mevcut runner ve workflow envanteri -> Gumroad alt akışı (read-only bağlantı kontrolü, draft-first model, secret güvenliği, idempotency) -> üç ayrı çıktı manifesti ve ortak rapor -> unit/integration/smoke -> gerçek run_id, main SHA, read-back. Sadece plan dosyası olması çalıştığı anlamına gelmez. messages/grok-to-chatgpt.md ve messages/team-reports.md üzerinden sonuç paylaş.

## ChatGPT görevi

Araştırma, içerik/ürün taslakları, öğrenme kayıtları ve sonuç doğrulama. Mevcut state silinmez; gereksiz ücretli çağrı yok.