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


## Araştırma kanalları — canlı envanter kontrolü, 2026-09-27

| Kanal | Bu kontrolde doğrulanan durum | Kullanım ve sınır |
| --- | --- | --- |
| Shopify | Bağlı mağazanın temel bilgisi tekrar okundu; Basic plan, EUR para birimi ve Türkiye mağaza ülkesi döndü | Bağlantı çalışıyor; bu okuma tek başına mağazanın herkese açık olduğunu, ürün/satış bulunduğunu veya satış hunisi verisi geldiğini kanıtlamaz. İlgili turda gereken Shopify analitiğini ayrıca oku. |
| Windsor.ai | Profil ve bağlı connector listesi okundu; Trial/non-paid profilinde YouTube, TikTok Organic, Instagram ve Facebook hesapları listelendi | Connector listesi hesap görünürlüğüdür, her platformdan güncel içerik/analitik verisinin döndüğü anlamına gelmez. Veri gerekiyorsa ilgili alanları keşfet ve read-only sorguyla doğrula. |
| YouTube Help / Studio | Resmi Analytics ve Shorts ölçüm sayfaları 2026-09-27'de açıldı | Kamuya açık metrikleri özel kanal retention/geliriyle karıştırma; özel veri yalnızca yetkili araç gerçek sonuç döndürürse kullanılır. |
| TikTok Creative Center | Resmi Trends yardım sayfası açıldı; Temmuz 2026 güncellemesi görüldü | Bölgesel/hashtag trendleri fikir sinyalidir; YouTube veya Shopify satış sonucunu kanıtlamaz. Ayrıntı giriş isteyebilir. |
| Meta Ad Library Search | Bu oturumda herkese açık Meta reklam arama aracı mevcut | Yalnızca gerçekten sorgulanıp sonuç döndüyse reklam mesajı/formatı için kullan; gösterim, satış veya dönüşüm sonucu çıkarma. Bu envanter kontrolünde sorgu yapılmadı. |
| Google Trends / Merchant Center | Google Trends metodoloji sayfası ve Merchant Center Popular Products dokümanı açıldı. Merchant Center hesabı/ürün feed'i doğrulanmadı. | Trends göreli 0–100 endeksi; Merchant Center raporu hesap gerektirir, Türkiye'yi destekler, iç kullanım şartlarına tabidir. |
| Ubersuggest / vidIQ | Mevcut tarihli kayıt korunuyor: ücretsiz Ubersuggest hesabında izlenen proje yok; vidIQ kredisi 0 | Yalnızca görevle ilgiliyse ve güncel hak/kota uygunsa kullan. Ücretli/kredi tüketen rutin sorgu yapma. |

Gelecek araştırmalarda her soruda en az bir uygun birincil/resmî web kaynağı kullan; varsa konuyla doğrudan ilgili bağlı kanalın verisini ikinci kanıt katmanı olarak doğrula. Kaynakları mekanik biçimde her turda topluca tarama: Shopify sorusunda Shopify/Google/Meta veya Merchant Center; Shorts sorusunda YouTube/Windsor/TikTok/YouTube arama kanallarından ilgili olanları seç. Kaynak, plugin veya hesap listede görünüyor diye kullanılmış sayma.



## Saatlik plan ve araştırma bağlantıları denetimi — 2026-09-27 12:30 TR

Read-only checks performed in this audit. No private performance numbers or account identifiers are recorded here.

| Connection / plan | Verified result | Limits / fix |
| --- | --- | --- |
| GitHub — `cerniva/ai-shared-workspace` | Repository metadata and research files were readable; repository is public and authenticated permissions include push. | Avoid placing private account metrics, emails, API keys, or tokens in this public repository. |
| Shopify | Read-only store-info call succeeded; connected store is Basic, EUR, Turkey, timezone +03. | This verifies the app connection only; it does not verify product, order, sales, or session analytics. |
| Windsor.ai | Live profile is Trial/non-paid; connected YouTube, TikTok Organic, Instagram, and Facebook accounts are listed. YouTube field discovery and a 7-day read both succeeded for date, video, views, engaged views, average view duration, and subscribers gained. | Do not store the returned private channel metrics in this public repo. `chose_to_view/swiped`, retention curves, and YouTube revenue were not returned in the field check; use authorized Studio/API data if a task truly needs them.
| Metricool | Read-only brand check confirmed the Cerno YouTube channel and Europe/Istanbul timezone. Scheduling tools are available in this session. | Daily video plan now prefers Metricool and verifies the scheduled post before reporting it. Buffer is visible in its website UI, but no Buffer connector is available in this tool session. Official guides are indexed in `SOURCES.md`. |
| Ubersuggest | Auth status previously confirmed for free tier. | No tracked project; use only free relevant keyword/SERP data, not paid reports. |
| TubeAlfred | In this audit, the public `trending_shorts` endpoint returned entries including long-form videos; the tool response charged 1 research credit and showed 49 remaining. | Do not treat that endpoint as a Shorts-only trend feed. Validate actual duration/format; use it only if a specific public example is worth the credit. A separate earlier query for professional cooking tips returned empty; do not repeat it. Credit balances are call-specific and can change. |
| Google Trends / Merchant Center / Search Console | Public Google Trends and official Merchant Center documentation are available; Merchant Center account and Search Console property/data were not verified in this audit. | These accounts are optional for public research. Flag them only when private store-search or Merchant Center account data is needed. |
| Saatlik Araştırma ve Kütüphane | Enabled, hourly, bound to this reporting conversation; it consults one highest-impact question and suppresses duplicate/no-change reports. | Older duplicate copy is paused; do not reactivate it. |
| Video ve Shopify Otomasyonu | Enabled daily at 16:00 Istanbul. | Research creates evidence/brief; this plan owns the video and publication workflow, preventing duplicate Shorts briefs. |
| Birleşik Finans, Kripto ve Küresel Piyasa Radarı | One enabled hourly instance. | Older duplicate instance is paused. It remains a separate finance scope. |

**Verimlilik kararı:** Saatlik araştırma her çalışmada tüm eklentileri taramaz. Önceki kaynak/rapor kaydını okur, bir derin araştırma sorusu seçer, uygun ücretsiz/gerçek erişilebilir kaynakları kullanır ve yalnızca yeni/karar değiştirici bulguyu raporlar. Her turda kaynak keşfi yapılır; ancak ekleme yalnızca kaynak doğrulanıp ilk kez yarar sağlıyorsa yapılır.


## Video ve Shopify otomasyonu denetimi — 2026-09-27 12:34 TR

- Shopify Analytics için yalnızca toplu oturum/sepet/checkout sorgusu başarıyla çalıştı; müşteri düzeyinde veri okunmadı veya kaydedilmedi. Bu, analitik okuma yolunun mevcut olduğunu doğrular; düşük örneklemden ürün/mağaza başarısı sonucu çıkarılmamalı.
- InVideo araçları görünür; mevcut proje/ajan bilgisi önceki read-only kontrolde listelendi, ancak üretim kredisi veya yayınlanabilir MP4 bu denetimde sınanmadı. Üretimden önce hesap/kredi koşulunu gerçek araç yanıtıyla kontrol et.
- Synthesia'da bu oturumun erişilebilir çalışma alanı yok; bu plana üretim yolu olarak eklenmemeli.
- Güncel araç listesinde Buffer aracı ve doğrudan YouTube yükleme/yayınlama aracı yok. Buffer hesabının Cerno kanalına bağlı görünmesi, bu sohbetten yükleme yetkisi sağlamaz. Yeni bir oturumda bu araçlar gerçekten görünmedikçe her gün yükleme denemesi yapma; MP4'ü teslim et ve kullanıcıya manuel yükleme adımını bildir.
