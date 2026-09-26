# Knowledge Ledger

Bu dosya, araştırmalardan çıkan ve sonraki görevlerde yeniden kullanılabilecek kısa, güncellenebilir öğrenmeleri tutar.

## Kayıt şablonu

### YYYY-MM-DD — Konu
- **Kaynak:** URL / dosya / video
- **Alan:** finance | youtube-growth | shopify | content | other
- **Ne öğrendik:** 
- **Kanıt düzeyi:** doğrulandı | kaynak iddiası | deney/yorum
- **Uygulama:** 
- **İlgili proje:** 
- **Son kontrol tarihi:** 
- **Not:** 

> Eski öğrenmeler sessizce silinmez. Geçersiz kalan bilgi tarih ve gerekçeyle güncellenir.

### 2026-09-26 — Ortak hafıza merkezi GitHub
- **Kaynak:** ai-shared-workspace canlı kurulum ve round-trip testleri
- **Alan:** other
- **Ne öğrendik:** Consumer sohbet oturumları ortak bağlamı otomatik paylaşmıyor; güvenilir ortak hafıza merkezi repo dosyaları olmalı.
- **Kanıt düzeyi:** doğrulandı
- **Uygulama:** TEAM_OPERATING_MODEL.md, PROTOCOL.md, reports/LATEST.md ve task dosyaları ortak bağlam olarak kullanılacak.
- **İlgili proje:** workspace
- **Son kontrol tarihi:** 2026-09-26
- **Not:** Kullanıcıya ajanların aynı sohbeti paylaştığı izlenimi verilmemeli.

### 2026-09-26 — Gemini API köprüsü
- **Kaynak:** GitHub Actions + Gemini API canlı testleri
- **Alan:** other
- **Ne öğrendik:** Gemini worker görevleri otomatik alıp GitHub'a sonuç döndürebiliyor; eski model adı 404 verdi, gemini-3.8-flash çalıştı; 503 için retry/backoff gerekli.
- **Kanıt düzeyi:** doğrulandı
- **Uygulama:** scripts/gemini_senses.py genel amaçlı worker olarak kullanılacak.
- **İlgili proje:** workspace
- **Son kontrol tarihi:** 2026-09-26
- **Not:** Canlı başarı mesajı BRIDGE_OK.

### 2026-09-26 — Görev kapasitesi ve overflow
- **Kaynak:** kullanıcı çalışma kuralı + ekip mimarisi
- **Alan:** other
- **Ne öğrendik:** Her ajan en fazla 5 aktif uygulama işi taşımalı; herkes görüş verir ama execution lead kapasite ve güçlü yöne göre seçilir.
- **Kanıt düzeyi:** doğrulandı
- **Uygulama:** docs/TASK_ROUTING.md ve tasks/agent_capacity.json ile takip.
- **İlgili proje:** workspace
- **Son kontrol tarihi:** 2026-09-26
- **Not:** ChatGPT dolduğunda kapasitesi olan backup ajana overflow.

### 2026-09-25 — YouTube Shorts ilk performans sinyali
- **Kaynak:** kanal performans ekranları
- **Alan:** youtube-growth
- **Ne öğrendik:** Bir Short yaklaşık 7 saatte 1.2K izlenmeye ulaştı ve trafiğin yaklaşık %98.2'si Shorts feed'den geldi.
- **Kanıt düzeyi:** doğrulandı
- **Uygulama:** hook/retention/format testlerini tekrar edilebilir seri haline getirmek.
- **İlgili proje:** content
- **Son kontrol tarihi:** 2026-09-26
- **Not:** O sırada retention verisi henüz bekleniyordu.

### 2026-09-25 — Shopify ürünleri draft aşamasında
- **Kaynak:** Shopify çalışma akışı
- **Alan:** shopify
- **Ne öğrendik:** Beş ürün draft olarak aktarılmış; ödeme yöntemi ve satışa açma zinciri tamamlanmadan canlıya alma ertelenmiş.
- **Kanıt düzeyi:** doğrulandı
- **Uygulama:** önce ödeme/checkout ve draft kontrolü, sonra yayın.
- **İlgili proje:** shopify
- **Son kontrol tarihi:** 2026-09-26
- **Not:** Bir otomasyon denemesi başarısız olduğundan son kontrol manuel doğrulama gerektiriyor.

### 2026-09-26 — YouTube Data API connector doğrulandı
- **Kaynak:** GitHub Actions canlı test YTTEST2
- **Alan:** youtube-growth | research
- **Ne öğrendik:** YOUTUBE_API_KEY ile çalışan YouTube connector canlı testte video başlığı, kanal, yayın tarihi, görüntülenme/beğeni/yorum sayıları, kanal istatistikleri ve yorum verilerini başarıyla çekti.
- **Kanıt düzeyi:** doğrulandı
- **Uygulama:** CORE-03 ve CORE-01 görevlerinde rakip kanal/video analizi, yorum madenciliği ve yapılandırılmış YouTube araştırması.
- **İlgili proje:** content / research-learning
- **Son kontrol tarihi:** 2026-09-26
- **Not:** İlk test import yolu nedeniyle başarısız oldu; import düzeltmesi sonrası PASS.

### 2026-09-26 — Dijital ürün teslim dosyası başlıkla eşleşmeli
- **Kaynak:** Shopify canlı ürün/dijital teslim dosyası okuması; kütüphanedeki SOP ZIP içeriği
- **Alan:** shopify
- **Ne öğrendik:** Mağazada dokuz ürünün tamamı draft. Yedi dijital ürünün dosyası bağlı; Restaurant & Café Operations SOP + Checklist Pack ürününe yanlışlıkla Restaurant_Reels_Hooks_PDF_DOCX.zip bağlanmış. Doğru Restaurant_Cafe_Operations_SOP_PDF_DOCX.zip dosyası mevcut ve içinde ilgili PDF ile DOCX doğrulandı.
- **Kanıt düzeyi:** doğrulandı
- **Uygulama:** Bu ürün yayınlanmadan önce yanlış ek kaldırılıp doğru ZIP bağlanmalı; ardından alıcı teslimi canlı olarak yeniden okunmalı. Her dijital üründe ürün vaadi, dosya adı ve ZIP içeriği birlikte kontrol edilmeli.
- **İlgili proje:** CORE-04 / shopify
- **Son kontrol tarihi:** 2026-09-26
- **Not:** Mevcut araçlar dosya ekleyebiliyor ama yanlış eki kaldırma işlemini sunmuyor. Sadece ikinci dosyayı eklemek hatayı çözmez.

### 2026-09-26 — Kullanıcının Gemini önceliği değişti
- **Kaynak:** kullanıcının son açık talimatı
- **Alan:** other
- **Ne öğrendik:** Gemini OAuth/ek kurulum işi beklemeye alındı; ChatGPT ve Grok ile somut CORE işlerine devam edilecek.
- **Kanıt düzeyi:** kullanıcı talimatı
- **Uygulama:** Gemini inbox idle ve görev yönlendirmesi güncellendi.
- **İlgili proje:** CORE-05 / workspace
- **Son kontrol tarihi:** 2026-09-26
- **Not:** İleride kullanıcı yeniden isterse mevcut köprü ayrıca değerlendirilebilir.
