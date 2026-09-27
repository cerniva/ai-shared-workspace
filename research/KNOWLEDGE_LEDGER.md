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

## Meta masa — 2026-09-26

| Tarih | Kaynak | Doğrulama | Durum |
|---|---|---|---|
| 2026-09-26 | docs/META_MANDATE.md | Okundu, 4 kişilik ekip | OK |
| 2026-09-26 | messages/from-meta.md | Append-only kanal | OK |
| 2026-09-26 | Push engeli | meta.ai push yok; Actions `GITHUB_TOKEN` yazar | Çözüldü (ingest/senses) |
| 2026-09-26 | META_MODEL_API_KEY | Actions secret | Eksik — Spark worker blocked |

### 2026-09-26 — Meta 4. üye + file-desk yazma
- **Kaynak:** META_MANDATE.md, from-meta.md, meta-senses.yml, meta-ingest.yml
- **Alan:** other
- **Ne öğrendik:** Consumer sohbetler ortak değil. Meta çıkışı `from-meta.md`. Push meta.ai'den gelmez; Action yazar. Model API hattı secret ister.
- **Kanıt düzeyi:** doğrulandı (worker need-key MSG-20260926-152241)
- **Uygulama:** görev `inbox-meta.md`; öğrenme `knowledge/meta-learnings.md`; şablon ortak-dil v1.2
- **İlgili proje:** workspace
- **Son kontrol tarihi:** 2026-09-26
- **Not:** META_BRIDGE_TOKEN / ikinci workflow yok.

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
- **Not:** Bir otomasyon denemesi başarısız olduğundndan son kontrol manuel doğrulama gerektiriyor.

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

### 2026-09-27 — Masa bildirimi poll-ledger, sohbet push değil
- **Kaynak:** https://docs.github.com/en/rest/activity/notifications?apiVersion=2022-11-28 (erişim 2026-09-27); https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow (erişim 2026-09-27); repo `scripts/desk_bridge.py`, `.github/workflows/grok-file-desk.yml`, `.github/workflows/tinyfish-event-bridge.yml`
- **Alan:** other
- **Ne öğrendik:** GitHub Notifications REST API bildirim yaratmaz, yalnız listeler/okundu işaretler. `GITHUB_TOKEN` ile açılan olaylar `workflow_dispatch` ve `repository_dispatch` dışında yeni workflow başlatmaz. PAT bir secret olur; istenmez. Bu yüzden secretsiz gerçek sohbet push'u yok. Çalışan yol, mesaj kimliği + geçiş anahtarıyla tekilleştirilmiş `state/message_delivery.json` defteri ve `desk-notify` koşucusudur.
- **Kanıt düzeyi:** doğrulandı (doküman + repo dosyaları; sohbet push testi yapılmadı)
- **Uygulama:** Yeni rapor pending, okuma seen, blocked olmayan yanıt answered, geciken okuma/ask tek delayed. `push=false` health kaydı olmadan canlı push iddia etme. `XAI_API_KEY` eksikliği Grok sohbetini kapatmaz; grok-api blocked yanıt üst ask'i answered yapmaz.
- **İlgili proje:** workspace
- **Son kontrol tarihi:** 2026-09-27
- **Not:** TinyFish `*/10` cron'u masa bildirimi değildir. Hızlı yol durur; ikinci hub yok.


### 2026-09-27 — xAI API 403: takım/izin kapısı
- **Kaynak:** https://docs.x.ai/developers/debugging (erişim 2026-09-27); https://docs.x.ai/overview (erişim 2026-09-27); repo `.github/workflows/grok-file-desk.yml`, `scripts/grok_senses.py`, `scripts/worker_adapters.py`.
- **Alan:** provider-reliability
- **Ne öğrendik:** xAI'nin resmî hata tablosunda HTTP 403, API key/team'in işlem izni olmaması veya team'in bloke olması anlamına gelir; 401 kimlik doğrulama, 404 ise model veya endpoint bulunamamasıdır. Güncel örnek `POST https://api.x.ai/v1/responses`, `Authorization: Bearer ...`, model `grok-4.7` kullanır. Mevcut Action logunda secret değeri GitHub tarafından maskelenmiş, model `grok-4.7`, sonuç 403'tür. Bu kanıt secret değerini görmeyi gerektirmez ve anahtarın hangi team/izne bağlı olduğunu tek başına belirlemez.
- **Kanıt düzeyi:** doğrulandı (xAI resmî docs + run 36280608297 logu + mevcut workflow/adapter kodu).
- **Uygulama:** İstek yolu/modeli dokümante edilmiş biçimde; 403'ü kodda körlemesine retry veya model değiştirerek aşmaya çalışma. `grok_senses.py` artık 403 için team/API izinlerini ve team blok durumunu kontrol etmeyi, anahtarı paylaşmamayı açıkça söyler. xAI Console takım erişimi değişmeden API worker'dan başarılı yanıt beklenmemeli.
- **İlgili proje:** TSK-20260927-001 / CORE-05.
- **Son kontrol tarihi:** 2026-09-27
- **Not:** API worker ve Grok consumer sohbeti farklı kanallardır. 403, consumer sohbetinin durumunu göstermez.

### 2026-09-27 — SOP teslim engeli kapandı; parola dönemindeki oturumlar satış testi değildir
- **Kaynak:** Shopify Digital Products canlı ürün okuması (2026-09-27); Shopify resmî yardım: https://help.shopify.com/en/manual/online-store/themes/password-page ve https://help.shopify.com/en/manual/reports-and-analytics/shopify-reports/overview-dashboard/using-the-overview-dashboard (erişim 2026-09-27).
- **Alan:** shopify
- **Ne öğrendik:** 2026-09-26 tarihli yukarıdaki SOP yanlış-ek kaydı tarihsel bulgudur. 2026-09-27 canlı okumada taslak SOP ürününün tek teslim eki `Restaurant_Cafe_Operations_SOP_PDF_DOCX 2.zip` (121510 bayt); yanlış Reels Hooks eki görünmüyor. Shopify resmî yardımına göre parola modu ürün sayfalarını ziyaretçi ve arama motorundan gizler; yönetici uygulamasından vitrin görüntüleme de oturum sayılabilir. 21–23 Eylül 2026 oturum ölçümü değişikliği dönemler arası kıyası ayrıca etkileyebilir.
- **Kanıt düzeyi:** Dosya ve taslak durumu canlı doğrulandı. Önceki yerel ZIP içerik doğrulaması yeni Shopify yüklemesinin içerik doğrulaması sayılmaz. Parola modu güncel repo durum kaydına dayanır; bu kontrolde vitrin ayrıca açılmadı.
- **Uygulama:** TSK-20260926-009 kapalı tutulur; SOP taslak kalır. Yeni ZIP'in içerik/teslim testi ile ödeme ve vitrin erişimi doğrulanmadan yayın önerilmez. Parola dönemindeki az sayıdaki oturumdan dönüşüm kararı çıkarılmaz.
- **İlgili proje:** CORE-04 / shopify
- **Son kontrol tarihi:** 2026-09-27
- **İzlenecek ölçüm:** Vitrin açıldıktan ve ödeme doğrulandıktan sonra gerçek dış trafik, sepete ekleme, checkout ve sipariş; aynı ölçüm tanımıyla dönem kıyası.
