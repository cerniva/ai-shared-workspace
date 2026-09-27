# Araştırma ve üretim araçları / bağlantı durumu

Son kontrol: **2026-09-27, Türkiye saati**. Bu dosya araç ile dış hesap erişimini ayırır. Araç listede görünmesi, ilgili hesabın veya her özelliğin çalıştığı anlamına gelmez. Sır, token, müşteri verisi ve hesap kimliği buraya yazılmaz. URL araştırma havuzu: [SOURCES.md](SOURCES.md).

## Bu turda gerçek okuma ile doğrulananlar

| Araç / bağlantı | URL | Kapsam ve kanıt | Kullanım / sınır |
| --- | --- | --- | --- |
| GitHub ortak depo | https://github.com/cerniva/ai-shared-workspace | Repo ve `research/SOURCES.md` okunup güncellendi | Rapor, hipotez, kaynak URL'si ve sonuç için kalıcı kayıt |
| Shopify | https://www.shopify.com/ | Bağlı mağazanın temel bilgisi okundu | Ürün ve gerçek mağaza analizi; vitrinin açık veya satışın başladığı sonucu çıkmaz |
| vidIQ | https://vidiq.com/ | Kullanıcının YouTube kanalı listelendi; 27 Eylül kontrolünde toplam kredi **0** | Kanala erişim var; kredi gerektiren transkript/Analytics/üretim çağrısı yapılmaz |
| Windsor.ai → YouTube | https://windsor.ai/ | YouTube kaynak hesabı listelendi; 24 Eylül tarihli bir videonun özel Analytics satırında views, engaged views, ortalama izleme süresi ve abone kazanımı gerçekten döndü | Shorts performansında ilk sıfır-vidIQ-kredili veri yolu; metrik/örneklem erişimini her tur doğrula, tüm Studio ölçümleri var sanma |
| Windsor.ai → TikTok, Instagram, Facebook | https://windsor.ai/ | Bu platformların bağlı kaynak hesapları listelendi | Hesap görünürlüğü doğrulandı; içerik/özel analiz okunup değerlendirilmiş sayılmaz |
| Metricool → YouTube | https://metricool.com/ | Markanın YouTube ağına bağlı kanal kimliği döndü | Planlama/analiz için aday; gerçek metrik kapsamı ayrıca sınanmalı |
| Descript | https://www.descript.com/ | Bir Cerno video projesi listelendi | Video düzenleme/proje erişimi var; o projenin bitmiş veya yayınlanmış video olduğu doğrulanmadı |
| InVideo | https://ai.invideo.io/ | “AI ile Shorts Üretimi - İlk Video” projesi ve içindeki ajan listelendi; üretimler listesi boş | Erişim var; mevcut projede hazır video/MP4 yok. Kullanıcı kredi koruma istediği için üretim çağrısı yalnızca yayınlanabilir brief ile ve bütçe koşulu doğrulanınca yapılır |

## 2026-09-27 ek bağlantı kontrolü

| Araç | URL | Doğrulanan durum | Sınır / sonraki adım |
| --- | --- | --- | --- |
| GitHub | https://github.com/cerniva/ai-shared-workspace | cerniva hesabı ve ortak repo okunuyor; kayıt dosyasına yazma çalışıyor | Ortak hafıza için kullan |
| Exa Search | https://exa.ai/ | Resmi YouTube Help sayfasını URL ve alıntıyla arayıp döndürdü | Web keşfi için kullanılabilir; özgün sayfa ayrıca doğrulanır |
| Ubersuggest | https://neilpatel.com/ubersuggest/ | Kimlik doğrulaması başarılı, ücretsiz hesap; izlenen proje listesi boş | Anahtar kelime/SEO araştırmasına aday; projeye özel izleme için proje kurulumu gerekir |
| Figma | https://www.figma.com/ | Hesap ve Starter takım görünüyor; koltuk türü View | Dosya açma/düzenleme/üretim yeteneği belirli bir dosyada ayrıca doğrulanmalı; tasarım üretildi sayılmaz |
| Synthesia | https://www.synthesia.io/ | Hesap kimliği doğrulandı fakat erişilebilir çalışma alanı listesi boş | Video üretimi kullanıma hazır değil; **FURKAN ELİNLE YAPMALISIN:** kullanmak istersen erişebildiğin bir çalışma alanını bağla/oluştur ve plan koşulunu kontrol et. Şimdi kredi/ücret harcanmadı |
| Görsel oluşturma | https://chatgpt.com/ | Bu oturumda görsel üretim aracı mevcut | Bu kontrolde görsel oluşturulmadı; proje brief'i ve kullanım hakkı gerektiğinde ayrı üretim |

Bu satırlar hesap durumu ile gerçek içerik erişimini ayırır; e-posta, anahtar ve özel hesap kimlikleri depoya yazılmaz.

## Kullanılan halka açık araştırma yolları

| Yol | URL | Kullanım |
| --- | --- | --- |
| Web araması ve resmi doküman | https://support.google.com/youtube/ | Güncel Shorts ölçüm, politika ve para kazanma açıklamaları; her iddiada özgün sayfa URL'si tutulur |
| YouTube video araması | https://www.youtube.com/results?search_query=shorts | Kamuya açık niş/format örnekleri; gerçek video izlenmediyse ilk kare veya kurgu incelenmiş gibi yazılmaz |
| Google Trends | https://trends.google.com/explore | Göreli arama ilgisi ve konu/ürün sinyali; satış hacmi değildir |
| TikTok Creative Center | https://ads.tiktok.com/creative/creativeCenter/trends | Çapraz platform trend fikri; YouTube başarısı kanıtı değildir |
| Shopify Help | https://help.shopify.com/ | Mağaza analitiği ve ürün/satış yöntemi |
| Akademik ve açık veri | https://openalex.org/works ; https://pubmed.ncbi.nlm.nih.gov/ ; https://datasetsearch.research.google.com/ | Konuya uygunsa özgün çalışma/veri setini bulup asıl kaynaktan doğrulama |

Ayrıntılı URL dizini ve saatlik kaynak ekleme kuralı [SOURCES.md](SOURCES.md) içindedir.

## Bağlantı adayı ve manuel kurulum

| Öncelik | Kaynak / bağlantı | URL | Beklenen veri | Durum ve Furkan'ın olası işlemi |
| --- | --- | --- | --- | --- |
| 1 | Google Search Console (mağaza için) | https://search.google.com/search-console/ | Arama sorgusu, tıklama, gösterim, sayfa performansı | Shopify sitesi Google hesabında doğrulanmış ve erişilebilir değilse **FURKAN ELİNLE YAPMALISIN:** site mülkiyeti doğrulamasını tamamla. ChatGPT için GSC Wizard eklentisi kurulu değil; seçersen eklenti bağlantısını da sen açarsın. |
| 2 | Google Merchant Center | https://merchants.google.com/ | Ürün görünürlüğü, tıklama ve uygunsa popüler ürün raporu | Hesap/ürün feed'i doğrulanmadı. **FURKAN ELİNLE YAPMALISIN:** uygun olduğunda Merchant Center hesabı ve Shopify ürün kaynağı bağlantısını kur; ödeme veya reklam bütçesi başlatma zorunluluğu yok. |
| 3 | Microsoft Clarity | https://clarity.microsoft.com/ | Isı haritası, oturum kaydı, sayfa sürtünmesi | Henüz mağazada kurulu/doğrulanmış değil. **FURKAN ELİNLE YAPMALISIN:** mağaza trafiği anlamlı seviyeye gelince hesap/site kurulumunu ve Shopify entegrasyonunu yetkilendir. Gizlilik/çerez yapılandırmasını kontrol et. |
| 4 | YouTube Studio | https://studio.youtube.com/ | Shorts'a özel izlemeyi seçme, kaydırma, retention ve para kazanma durumu | Windsor bazı özel ölçümleri döndürüyor; Studio'nun tüm ekranları veya doğrudan yükleme yetkisi doğrulanmadı. **FURKAN ELİNLE YAPMALISIN:** eksik ölçümler için Studio erişimini bağla ya da ilgili ekranı paylaş. |

## Kullanım kuralı

1. İşe göre en kısa veri yolunu seç; aynı YouTube ölçümünü vidIQ kredisi harcayarak tekrar isteme. Önce Windsor'da erişilebilen metrikleri, sonra yalnızca eksikse Studio/başka bağlantıyı araştır.
2. Her gerçek kullanımı tarih, kaynak hesabının adı, sorgulanan dönem, metrik, kaynak URL'si ve sınırla raporla. Bağlı uygulama görünmesi ile gerçek veri okunmasını karıştırma.
3. Saatlik araştırmada mevcut [SOURCES.md](SOURCES.md) URL'lerini ve eski deneyleri oku; değerli yeni kaynağı doğrulayınca URL dizinine ekle. Bir sonraki Shorts/video veya Shopify kararında kanıta bağla.
4. Kredili video aracı yalnızca yayınlanabilir üretim için ve kullanıcının kredi koruma talimatına uygun kullanılır. Özel hesap bilgilerini açık depoya yazma.

## Remote Desktop Commander kontrolü — 2026-09-27

Eklenti yönetiminde Remote Desktop Commander **installed=true** görünüyor. Kullanıcı henüz bilgisayar almadığını belirtti; yerel cihaz bağlantısı istenmeyecek. Eklentinin dosya/terminal yetenekleri bu oturumda görünmedi ve cihaz okunmadı. Telefon ve mevcut bulut bağlantıları kullanılacak. GSC Wizard eklentisi kurulu; Search Console mülkü/verisi doğrulanmadı.

## GSC Wizard kurulum kontrolü — 2026-09-27

Eklenti yönetimi **installed=true** döndürdü. Bu oturumun çağrılabilir araç listesinde GSC Wizard aracı henüz görünmedi; Search Console mülkü veya gerçek performans satırı okunamadı. Kurulum sonrası yeni oturumda read-only mülk listesiyle doğrulama gerekir.

## Buffer, Supabase ve Vercel — 2026-09-27

| Bağlantı | URL | Durum | Sınır |
| --- | --- | --- | --- |
| Buffer → Cerno YouTube | https://publish.buffer.com/settings/channels | Güvenli girişten sonra Buffer ayarlarında Cerno YouTube Channel, 1/3 bağlı kanal ve Free plan görüldü | ChatGPT Buffer eklentisi yok; MP4 yükleme, zamanlama ve otomatik yayın bu kontrolde yapılmadı |
| Supabase | https://supabase.com/ | Kullanıcı eklenti bağlantısını tamamladı | Bu oturumda çağrılabilir aracı olmadığı için hesap/proje erişimi sınanmadı |
| Vercel | https://vercel.com/ | Kullanıcı eklenti bağlantısını tamamladı | Bu oturumda çağrılabilir aracı olmadığı için hesap/proje erişimi sınanmadı |

Bu bağlantıları görevle eşleştirirken önce read-only proje/hesap kontrolü yap; sır veya token kaydetme.


## Windsor / YouTube Analytics gecikme kuralı — 2026-09-27 12:10 TR

- Resmi kaynak: https://developers.google.com/youtube/analytics/data_model?hl=en (son güncelleme 2026-09-14 UTC).
- YouTube Analytics API verisi gerçek zamanlı değildir; tipik gecikme 48–72 saattir. Windsor'da yeni video için boş Analytics satırı bağlantı arızası veya sıfır performans olarak etiketlenmez.
- Kamu video metadata'sı güncel views/likes/comments kontrolüne yarar; engaged views, AVD/APV, retention veya gelir yerine kullanılmaz.
- Yeni video özel ölçümü için ilk karar penceresi 48–72 saat; saatlik kontrolde aynı boş sorgu sonucu yeni bulgu diye çoğaltılmaz.


## Araştırma bağlantıları — 2026-09-27 kaynak denetimi

| Araç / kanal | Gerçek kontrol | Kullanım ve sınır |
| --- | --- | --- |
| Exa Web Search | Resmî YouTube, Google Trends ve Google Search Central sayfalarını bulmak için kullanıldı; özgün URL'ler web aramasında açılarak kontrol edildi. | Kaynak keşfi için kullan; Exa sonucu nihai kanıt sayılmaz, özgün sayfayı aç. |
| Windsor.ai | Bağlı kaynak listesi yeniden okundu: YouTube ve TikTok Organic hesapları görünür. Bu turda metrik verisi çekilmedi. | Hesap listelenmesi Analytics verisinin okunduğunu kanıtlamaz; her veri sorgusunda hesap, dönem ve dönen alanları ayrı doğrula. |
| TubeAlfred YouTube Search | 2026-09-27'de “professional cooking tips” sorgusu, son 1 ay Shorts/popularity filtresiyle çalıştırıldı; boş sonuç verdi ve 1 kredi kullandı (yanıtta 47 kredi kaldığı bildirildi). | Aynı sorguyu tekrar etme. Yalnızca somut niş örneği gerektiğinde ve kredi maliyetini gözeterek kullan; boş sonuçtan trend çıkarma. |

Kredi notu: Bu denetimde TubeAlfred'e ait 1 araştırma kredisi kullanıldı; video üretim kredisi kullanılmadı. Bağlı araştırma araçlarını tekrar/boş sorgu için çağırma.
