# Bilgi Kütüphanesi | 2026-09-28 05:58 TRT

## ÖNEMLİ GMAIL BİLDİRİMİ
- GitHub bildirimi doğrulandı: PR [#28](https://github.com/cerniva/ai-shared-workspace/pull/28) birleşti ve ortak makine-okunur öğrenme defteri ana dala eklendi. Worker testleri ile CodeQL başarılı; CodeRabbit durumu hâlâ pending, tamamlanmış inceleme gibi değerlendirilmedi.

## YENİ KAYNAKLAR
- [Choosing permissions for a GitHub App](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app): GitHub’ın resmî belgesi. Uygulamaların varsayılan olarak izinsiz olduğunu, minimum izin seçilmesi gerektiğini ve Contents ile Workflows yetkilerinin ayrı olduğunu doğruluyor. Merkezi kimlik: `src_a2ab2e6f41d05d70`.

## GÜNCELLENEN/TEKİLLEŞTİRİLEN KAYNAK
- Merkezi kaynak kataloğu 7 benzersiz canonical URL’ye çıktı. Yeni URL ve sabit kimlik için dedup kontrolü ve yazma sonrası geri okuma geçti.
- Makine öğrenme defterine `learn_b1ce3ec3c7f9abbf` eklendi; defterde 2 benzersiz kayıt var ve kaynak referansı geçerli.

## YENİ BİLGİ
- Bilgi Kütüphanesi planı için hem kaynak kataloğu hem öğrenme defteri üzerinde gerçek read → dedup → write → read-back tamamlandı.
- GitHub App’in kurulu görünmesi yeterli değil: kod/dosya erişimi için Contents, Actions iş akışlarını düzenlemek için ayrıca Workflows izni gerekir.

## KAYDEDİLEN DERS/KAYIT ENGELİ
- SOURCES.md, bağlantı envanteri, Markdown öğrenme defteri ve makine-okunur öğrenme defteri güncellendi.
- Engel: Finance, Video-Shopify ve Sistem planlarının kendi köprü testleri yok; otomatik aktarım yaptıkları varsayılmıyor.

## SONRAKİ KEŞİF
- Bir sonraki aktif planda kaynak + öğrenme çiftini tekilleştirerek plan bazlı ilk köprü testini doğrulamak.

---

# Bilgi Kütüphanesi | 2026-09-28 05:22 TRT

## YENİ KAYNAKLAR
- [GitHub OAuth app scope’ları](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps): Resmî belge açılarak doğrulandı. `repo` kapsamının özel/açık depolarda geniş okuma-yazma, `workflow` kapsamının Actions iş akışı dosyalarını ekleme/güncelleme yetkisi verdiğini açıklar; bağlı uygulamalara fiilen verilen izinleri göstermez. Merkezi kimlik: `src_f0d89c2d1756987d`.
- [Shopify ödeme sağlayıcısı kullanılabilirliği](https://help.shopify.com/en/manual/payments/third-party-providers/payment-gateway-availability): Resmî sayfa yeniden açıldı. Shopify, ülkeye göre güncel sağlayıcı listesinin birincil kontrol noktası olduğunu; Admin’de görünen seçeneklerin mevcut ödeme yapılandırmasına göre farklılaşabileceğini belirtiyor. Bu belge iyzico başvuru/onay kanıtı değildir. Merkezi kimlik: `src_7fdeed3f9ddd8166`.

## GÜNCELLENEN/TEKİLLEŞTİRİLEN KAYNAK
- PR [#27](https://github.com/cerniva/ai-shared-workspace/pull/27) ana dala birleşti. İki önceki GitHub izin kaynağı, yeni OAuth scope kaynağı ve Shopify ödeme kaynağı canonical URL + sabit `source_id` ile merkezi `knowledge/source_catalog.json` kataloğuna aktarıldı.
- Yazma sonrası geri okuma geçti: katalogda 6 kaynak ve 6 benzersiz canonical URL var; ikinci kopya oluşmadı.

## YENİ BİLGİ
- “PR birleşti” ile “plan gerçekten bağlı” ayrımı test edildi: Bilgi Kütüphanesi planı için read → dedup → write → read-back yolu doğrulandı. Bu, diğer aktif planların otomatik kaynak aktarımını henüz kanıtlamıyor.
- OAuth kaynakları için karar farkı: yalnız uygulama adını görmek yeterli değil; `repo`, `workflow`, organizasyon ve yönetim kapsamları ayrı risk yüzeyleri olarak değerlendirilmelidir.

## KAYDEDİLEN DERS/KAYIT ENGELİ
- SOURCES.md, TOOLS_AND_CONNECTIONS.md ve KNOWLEDGE_LEDGER.md tarihli yeni durumla güncellendi; eski 04:10 kaydı silinmedi, geçersizleştiği açıkça işlendi.
- Kalan engel: bridge doğrulayıcısı `related_plan`, `account_requirement`, `why_valuable`, `last_verified_at` alanlarını ve istenen `available_unverified/web_only/quota_limited` durum adlarını henüz desteklemiyor.

## KAYNAK AÇIĞI
- Diğer aktif planlar için plan bazlı köprü testi yok; onların önceki kaynak adayları otomatik aktarılmış sayılmıyor.
- Mevcut GitHub uygulamalarına verilmiş gerçek OAuth/GitHub App izin listesi okunmadı; resmî doküman yalnız denetim yöntemini ve kapsam anlamlarını doğruluyor.

## SONRAKİ KEŞİF
- Bridge şemasını eksik metadata/erişim durumlarıyla uyumlu hale getirip bir aktif planda ilk gerçek read → dedup → write → read-back entegrasyonunu doğrulamak.

---

# Bilgi Kütüphanesi | 2026-09-28 04:10 TRT

## ÖNEMLİ GMAIL BİLDİRİMİ
- **Ortak bilgi köprüsü:** PR #27 açık, birleştirilmemiş. Head commit için test ve CodeQL başarıyla tamamlanmış; CodeRabbit'in son yorumu incelemenin sürdüğünü söylüyor. Diğer planların kaynakları otomatik içe aktarılıyor denemez.
- **HeyGen:** “Mbappé: Biliyor muydun?” videosu 19 sn / 720p / 11.7 MB olarak hazır bildirildi. E-posta “3 gündür hazır” diyor; indirme veya YouTube yayını doğrulanmadı. HeyGen aracı bu oturumda dosyayı almaya yetecek sessionId sunmadı.
- **Polar Analytics:** Google bildirimi yalnız ad, profil resmi ve e-posta paylaşımını doğruluyor; Shopify/Analytics erişimi değil.

## YENİ KAYNAKLAR
- [GitHub: authorized OAuth apps](https://docs.github.com/en/apps/oauth-apps/using-oauth-apps/reviewing-your-authorized-oauth-apps) ve [GitHub Apps izinlerini gözden geçirme/iptal](https://docs.github.com/en/apps/using-github-apps/reviewing-and-revoking-authorization-of-github-apps). Exa ile keşfedildi, özgün sayfalar 28 Eylül’de açıldı; resmi doküman. Kaynak kayıtlarında URL ve amaçla dedup kontrolü yapıldı.

## GÜNCELLENEN/TEKİLLEŞTİRİLEN KAYNAK
- İki GitHub güvenlik belgesi yeni, tekil kart olarak kaynak kataloğuna eklendi. Exa/GitHub/Gmail'in gerçek kullanım durumu araç envanterine işlendi.

## YENİ BİLGİ
- PR #27’nin otomasyon testleri ve CodeQL’i başarılı; bu yalnız PR koduna ilişkin CI kanıtı. PR açık olduğu ve plan-bağlantı testleri bulunmadığı için merkezi köprü etkin sayılmıyor.
- Önerilen kaynak şemasında kütüphanenin beklediği bazı metadata alanları ve erişim statüleri eksik. Bu uyumsuzluk çözülmeden diğer planlara otomatik kaynak aktarımı yapılamaz.

## KAYDEDİLEN DERS/KAYIT ENGELİ
- Köprü PR #27’nin durumu, güven sınırları ve sonraki kontrolü Knowledge Ledger’a yazıldı. Engel: PR ana dala alınmamış, şema uyumu ve plan başına read/write/read-back testi yok.

## KAYNAK AÇIĞI
- Polar Analytics mağaza verisi yok; Google SSO bildirimi yalnız temel profil iznini gösteriyor.
- HeyGen çıktısı e-postada hazır görünse de dosya indirme/yayın durumu erişilebilir araçla doğrulanmadı.

## SONRAKİ KEŞİF
- PR #27’nin merge/CodeRabbit sonucu; ardından bridge alan eşlemesi ve plan başına gerçek read/write/read-back testi. Gmail’deki hassas doğrulama kodları veya tokenlar rapor/kataloğa alınmadı.

# Araştırma farkı — 27 Eylül 2026, 12:10 Türkiye saati

- YouTube'un resmi Analytics API veri modeli, özel Analytics verisinin gerçek zamanlı olmadığını ve tipik 48–72 saat geciktiğini doğruladı. Windsor'da uçak ve Bitcoin Short'larının boş satırı artık sıfır performans değil “işlenmiş veri hazır değil” olarak sınıflandırılıyor.
- Kamu video metadata değerleri ve Mbappé özel ölçümü önceki kontrolden değişmedi. Stayed-to-watch/swiped, retention eğrisi, YPP ve gelir verisi yok.
- Shorts deneyi değişmedi: süreli futbol quiz brief'i korunuyor. Uçak videosu 28 Eylül 16:04 TR, Bitcoin videosu 29 Eylül 02:21 TR sonrasında ölçülecek.
- Shopify hunisinde yeni doğrulanmış hareket veya ürün-talep kanıtı yok; fiyat, yayın, ödeme veya tema değişikliği yapılmadı.
- Exa ile iki hedefli aramada 14 sonuç incelendi; Google'ın özgün resmi belgesi açılarak doğrulandı. Figma hesabı Starter/View olarak tekrar okundu; tasarım değişikliği yapılmadı.
- app-6a6c6ebc8f74819197497c772358751b için çağrılabilir araç yine görünmedi; erişim var sayılmadı.

---

# Araştırma farkı — 27 Eylül 2026, 09:00 Türkiye saati

- Windsor iki yeni yayımlanmış Short'u kamu metadatasında gördü; özel Analytics iki yeni video için henüz veri döndürmedi. En yeni video yaklaşık 10 saatlik ve örneklem çok küçük olduğu için başarısız sayılmadı.
- Mbappé Short'unun özel ölçümü değişmedi; önceki bulgu tekrar yeni sonuç diye yazılmadı. Studio'ya özgü stayed-to-watch/swiped ve retention eğrisi hâlâ yok.
- 2026 futbol quiz örneklerinde ilk karede süreli görev/cevap tahmini formatı görüldü. Bir sonraki brief için tek değişken: 3 saniyelik tahmin süresi ve “kaçıncı saniyede bildin?” yorumu.
- USDA Food Buying Guide ve USDA ARS pişirme verimi kaynakları doğrulandı. Food Cost kararı “sabit verim tablosu”ndan “kaynak etiketli başlangıç değeri + işletmenin kendi ölçümüyle override” yapısına daraltıldı.
- Shopify hunisinde yeni sepet, checkout, sipariş veya satış sinyali yok. Fiyat, yayın, ödeme veya canlı tema değişikliği yapılmadı.
- Figma kimliği tekrar doğrulandı: Starter/View; dosya anahtarı olmadığı için tasarım değişikliği yapılmadı. Seçilen app-6a6c6ebc8f74819197497c772358751b için bu oturumda çağrılabilir araç görünmedi; erişilmiş sayılmadı.
- Sonraki kontrol: Bitcoin Short'u 72 saatini doldurduktan sonra 29 Eylül 02:21 TR sonrası; Food Cost taslağına dosya erişimi oluştuğunda.

---

# Araştırma farkı — 27 Eylül 2026, 08:05 Türkiye saati

- Windsor YouTube veri yolu yeniden çalıştı ve yayımlanmış Short için video düzeyinde views, engaged views, ortalama izleme süresi/yüzdesi, etkileşim ve abone değişimi döndürdü. Özel kanal sayıları herkese açık repoya kaydedilmedi.
- YouTube'un 19 Ağustos 2026 resmi engaged-view açıklamasıyla metrik anlamı çapraz kontrol edildi. Stayed-to-watch/swiped ve retention eğrisi dönmedi; bunlar varmış gibi yorumlanmadı.
- Food Cost adayında karar daraltıldı: sıradan reçete maliyet tablosu yerine satın alma birimi → yenilebilir verim/fire → porsiyon → fiyat akışı doğrulanmalı. Rakip kaynakta yield özelliğinin bulunmadığı açıkça görüldü; bu yalnız farklılaşma adayıdır, talep/satış kanıtı değildir.
- Figma hesabı Starter/View koltuğuyla doğrulandı; belirli dosya anahtarı olmadığı için tasarım okunmadı veya üretilmedi.
- Sonraki kontrol: Short 72 saati doldurduktan sonra ölçümü yenile; Shopify adayını dosya içeriği erişince veya 4 Ekim haftalık incelemede yeniden değerlendir.

---

# Bugünkü denetim — 27 Eylül 2026, 07:30 Türkiye saati

## Kontrol edilen durum ve yapılan düzeltmeler

- **Buffer → Cerno YouTube:** Buffer Channels ekranında Cerno YouTube Channel bağlı; Free planda 1/3 kanal kullanılıyor. Bu ekranda kuyruk veya gönderilmiş video kontrol edilmedi; bugün Buffer üzerinden yayın yapıldığı doğrulanmadı.
- **Supabase ve Vercel:** Eklenti bağlantı akışları tamamlandı. Bu oturumda eklenti araçları görünmediği için hesap/proje erişimi ayrıca doğrulanamadı; sır veya erişim anahtarı kaydedilmedi.
- **Saatlik Araştırma ve Kütüphane:** Etkin, saatte bir. Son çalışma kaydı 05:57 Türkiye saati. Buffer bağlantı notunu okuması ve tetiklemenin sürekli izleme olmadığını belirtmesi eklendi.
- **Shorts Viral Lab:** Etkin, her gün 16:00 Türkiye saati. Son çalışma kaydı 26 Eylül 19:19; 27 Eylül 16:00 çalışması henüz gelmedi. Buffer bağlı kanalını yayın yolu olarak kontrol etmesi; yükleme/kuyruk durumunu doğrulamadan yayımlandı dememesi eklendi. Bugün için tamamlanmış MP4 veya yayın doğrulaması yok.
- **Birleşik Finans, Kripto ve Küresel Piyasa Radarı:** Etkin, saatlik. Bu görev anlık olay akışı sağlayamaz; her çalıştırma arasındaki gelişme gecikebilir. Son kontrolden bulunan önemli olayların ayrı maddelerle, olay saati ve kaynakla aktarılması; saat içi/anlık izleme garantisi verilmemesi eklendi.
- **Kayıt düzeltmesi:** `research/TOOLS_AND_CONNECTIONS.md` Buffer, Supabase ve Vercel durumlarını içeriyor. `research/PLUGIN_INVENTORY.md` envanter satırları ve eski 124/2750 sayısının güncel toplam olmadığı notuyla düzeltildi. Bu rapor eski içerik korunarak öne eklendi.

## Açık sınırlamalar

- Buffer web hesabında kanal bağlantısı doğrulandı; Buffer’dan YouTube’a gerçek MP4 yükleme/yayınlama bu denetimde denenmedi. Günlük otomasyon çalışınca o görevde Buffer erişimi ve MP4 üretim/yayın adımları ayrıca doğrulanmalı.
- Supabase ve Vercel’de bağlantı kurulmuş görünse de bu oturumda proje listesi okunmadı.
- Birleşik finans radarı en fazla saatlik tetiklenir; önemli gelişme için sıfır gecikme garanti edilemez.
- Saatlik çalışma kaydı, o saatteki tetiklemenin çalıştığını gösterir; her araştırma iddiasının ve dış eylemin tamamlandığını tek başına kanıtlamaz.

**Manuel adım:** Şu anda kullanıcıdan bilgisayar kurulumu veya başka bir elle işlem gerekmiyor.

---

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
