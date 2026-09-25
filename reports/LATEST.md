# 3 Günlük Ekip Raporu — 24–26 Eylül 2026

## 1) Son 3 günde yapılanlar

### Ortak çalışma sistemi
- `cerniva/ai-shared-workspace` üçlü çalışma masasının ana reposu olarak kuruldu.
- ChatGPT = koordinasyon/sol beyin, Grok = alternatif bakış/sağ beyin, Gemini API = duyu organları + genel analiz olarak tanımlandı.
- `TEAM_OPERATING_MODEL.md`, `PROTOCOL.md`, `tasks/active.json`, mesaj kanalları ve durum dosyaları oluşturuldu/güncellendi.
- Sürekli iş havuzu 5 ana göreve indirildi.
- PayoutLens ayrı ürün/repo olarak korunuyor: `cerniva/grok-chatgpt-masa`.

### Gemini API köprüsü
- `messages/inbox-gemini.md` görev kutusu
- `scripts/gemini_senses.py` worker
- `.github/workflows/gemini-senses.yml` workflow
- `messages/gemini-to-chatgpt.md` çıktı kanalı
- `research/youtube/` video araştırma klasörü
kuruldu.
- `GEMINI_API_KEY` repository secret eklendi.
- İlk testte eski model adı nedeniyle 404 görüldü; model `gemini-3.8-flash` olarak güncellendi.
- Google tarafındaki geçici 503 yoğunluk hataları için retry/backoff eklendi.
- Canlı test başarıyla geçti: `BRIDGE_OK / rol: duyu organı / durum: hazır`.
- Worker artık yalnızca YouTube değil; finans, yazılım, Shopify, araştırma, içerik, eleştiri ve problem çözme gibi genel görevleri de alabiliyor.

### Araştırma/öğrenme altyapısı
- `research/SOURCES.md` oluşturuldu.
- `research/KNOWLEDGE_LEDGER.md` oluşturuldu.
- Öğren → doğrula → kaydet → uygula → güncelle döngüsü tanımlandı.
- YouTube/transcript, resmi kaynaklar, web/haber, sosyal/topluluk ve uzman görüşleri araştırma katmanları olarak tanımlandı.
- Önemli açık: Knowledge Ledger henüz gerçek öğrenmelerle yeterince doldurulmadı; öncelikli yapılacak işlerden biri bu.

### Shopify / gelir tarafı
- Shopify mağazası üzerinde çalışıldı.
- Beş ürün Shopify'a draft olarak aktarılmış durumda; ödeme yöntemi onayı tamamlanmadan canlıya alma ertelendi.
- Bir otomasyon denemesi başarısız oldu; draft ürünler ve satışa açma akışı yeniden gözden geçirilmeli.
- PayoutLens ayrı SaaS olarak korunuyor.
- Shopify/e-ticaret için ürün araştırması, dönüşüm, SEO, fiyat/teklif ve dijital ürün katmanı ana görev haline getirildi.

### YouTube / içerik tarafı
- Shorts üretim ve büyüme sistemi üzerinde çalışıldı.
- Bir Short yaklaşık 7 saatte ~1.2K izlenmeye ulaştı; trafiğin ~%98.2'si Shorts feed'den geldi.
- Retention verisi o sırada henüz oluşmamıştı.
- Kapak/başlık, hook, retention, tekrar izleme, Shorts formatı ve trend araştırması çalışma alanına alındı.
- vidIQ, Metricool ve video üretim araçları gibi bağlantılar değerlendirildi/kullanıma alındı.

### Finans / piyasa araştırması
- Finans, makro, şirketler, kripto ve yatırım eğitimi ayrı sürekli görev haline getirildi.
- FinancialFilings, HYPD AI, Supermetrics gibi veri/analiz kaynakları bağlandı veya devreye alındı.
- Kullanıcı özellikle altcoin boğası, kripto projeleri, makro göstergeler, şirket haberleri ve olayların hisselere etkisini takip etmek istiyor.
- Ana kural: YouTube/yorum/tahmin ayrı, doğrulanmış veri ayrı tutulacak.

### Bağlantılar / araçlar
Son 3 günde GitHub, Notion ve çeşitli üretim/analiz araçlarıyla çalışma altyapısı genişletildi. Öne çıkanlar:
- GitHub Codex Connector
- FinancialFilings
- HYPD AI
- Supermetrics
- Runway
- vidIQ
- Metricool
- Dropbox
- Canva/Notion/GitHub odaklı üretim akışı

## 2) Öğrendiklerimiz

1. Aynı model ailesindeki normal consumer sohbet ile API worker aynı hafızayı paylaşmaz.
2. Ortak bağlamın güvenilir merkezi GitHub workspace olmalı.
3. API anahtarları repo veya sohbete yazılmamalı; secret store kullanılmalı.
4. Ajanlardan biri erişemediğinde iş mümkünse diğer ajana/araça yönlendirilmeli.
5. Geçici API hataları için retry/backoff şart.
6. Bir bağlantının gerçekten çalıştığı yalnızca canlı round-trip testiyle kabul edilmeli.
7. Üç ajanın ham çıktısını kullanıcıya yığmak yerine ChatGPT sentezlemeli.
8. Tek seferlik araştırma yeterli değil; faydalı öğrenmeler Knowledge Ledger'a işlenmeli.
9. Görev sayısı kontrolsüz büyümemeli; 5 ana iş havuzu korunmalı.
10. Shopify, içerik ve finans çalışmalarında araştırma → uygulama → ölçüm döngüsü kurulmalı.

## 3) Aktif 5 ana görev

- CORE-01 — Araştırma & Öğrenme Motoru
- CORE-02 — Finans & Piyasa İstihbaratı
- CORE-03 — İçerik & YouTube Büyüme Motoru
- CORE-04 — Shopify / Ürün / Gelir Motoru
- CORE-05 — Sistem, Araçlar & Otomasyon Geliştirme

## 4) Öncelikli açık işler

- Grok için Gemini'deki kadar otomatik API köprüsü henüz yok; bu yüzden Grok otomatik overflow worker seviyesinde değil.
- Knowledge Ledger gerçek öğrenmelerle doldurulmalı.
- Günlük ekip raporu ve görev kapasite sistemi kalıcı hale getirilmeli.
- Shopify draft ürünler, ödeme yöntemi ve satışa açma zinciri tamamlanmalı.
- YouTube üretim hattında performans verisine göre tekrar edilebilir formatlar çıkarılmalı.
- Finans araştırmasında günlük/haftalık kaynak ve doğrulama rutini kurulmalı.
- Bağlanan araçlardan hangilerinin gerçekten değer ürettiği ölçülmeli; gereksiz bağlantılar azaltılmalı.

## 5) Yeni çalışma kuralı

- Her ajan için en fazla 5 aktif iş slotu.
- Yeni görev geldiğinde tüm ekip görüş verir.
- Uygulama lideri, görevin türü + erişim + mevcut kapasiteye göre seçilir.
- Bir ajanın 5 slotu doluysa yeni uygulama işi kapasitesi olan diğer ajana geçer.
- Gemini API otomatik başlayabilir.
- Grok'a görev repo üzerinden bırakılabilir; Grok'un tam otomatik başlaması için ayrıca xAI/Grok API köprüsü gerekir.
- ChatGPT son sentez, doğrulama ve kullanıcıya raporlama sorumluluğunu korur.

## 6) Önerilen uzmanlık liderliği — taslak

- ChatGPT: koordinasyon, doğrulama, sentez, araçlar arası orkestrasyon, nihai çıktı
- Grok: yaratıcı strateji, alternatif fikir, trend, red-team, ürün/konsept varyasyonları
- Gemini API: medya/video/transcript, uzun bağlam analizi, bağımsız araştırma, ikinci/üçüncü teknik görüş

Bu liderlik sınır değildir; üçü de tüm alanlarda çalışır.

## 7) Ekipten istenen geri bildirim

Grok ve Gemini'den:
- Bu rapordaki eksik/yanlış noktaları işaretleyin.
- 5 CORE görev için hangi ajan lead / backup olmalı önerin.
- Her ajan için en verimli 3–5 iş tipini belirtin.
- ChatGPT dolduğunda overflow sırasını önerin.
- Günlük raporda hangi metriklerin zorunlu olması gerektiğini belirtin.
