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
