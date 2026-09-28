# Google + YouTube Kaynak Yönlendirme ve Görev Dağılımı Tasarımı

Tarih: 2026-09-28
Durum: Tasarım onayı bekliyor
Kapsam: `cerniva/ai-shared-workspace` ortak araştırma, içerik, commerce ve sistem planlarının kaynak/ajan yönlendirmesi
Korunan kapsam: PayoutLens'e dokunulmaz

## 1. Amaç

Bağlı araçları tek bir güvenilir görev dağılımına toplamak; Google ve YouTube'u resmi olarak kaynak havuzuna eklemek; aynı araştırmanın farklı araçlar tarafından tekrar edilmesini azaltmak; Shorts araştırma→üretim→yayın→analiz döngüsünü daha kapsamlı ve doğrulanabilir yapmak.

Başarı ölçütleri:
- Her kaynak/araç için net görev ve güven sınırı bulunur.
- Google keşif kaynağıdır; tek başına kanıt değildir.
- YouTube hem içerik/format keşfi hem resmi kanal kaynağı olarak kullanılır; kanal performansı için bağlı analytics kaynakları önceliklidir.
- Kendi kanal verisi, genel YouTube araştırması ve yayın hattı birbirinden ayrılır.
- Ortak `knowledge/source_catalog.json` dedup merkezi olur.
- `tasks/active.json` görev sahipliği ve yedek rollerini daha ayrıntılı taşır.
- `state/now.json` yalnız canlı doğrulanmış bağlantı/sağlık durumunu tutar.
- Aktif otomasyonlar aynı yönlendirme kurallarını kullanır.

## 2. Kaynak ve araç rolleri

### ChatGPT
Orkestrasyon, sentez, karar, güvenlik sınırı, kod/değişiklik, son doğrulama ve görev birleştirme.

### TinyFish
Birincil browser/web worker. Google/web keşfi, dinamik sitelerde gezinme, form/tıklama gereken web işleri ve kayıtlı Browser Context Profile oturumları. Başarı yalnız gerçek run sonucu/read-back ile doğrulanır.

### Google Search
Yeni kaynak, trend, rakip, ürün, teknik çözüm ve resmi sayfa keşfi. Arama sonucu/snippet tek başına kanıt sayılmaz; kritik iddia mümkünse resmi/birincil kaynaktan doğrulanır.

### YouTube
- Resmi YouTube/Creator/Help kanalları: birincil platform rehberi.
- Genel videolar/kanallar: içerik formatı, hook, tema ve rakip keşfi için örneklem.
- Tek creator videosu finansal/teknik gerçek için bağımsız kanıt sayılmaz.

### vidIQ
YouTube keyword, trend, rakip kanal/video, SEO ve büyüme sinyalleri. İçerik seçiminde yardımcı nicel/rekabet kaynağıdır; kanalın kesin performans kaydı yerine bağlı kanal analytics verisi tercih edilir.

### Metricool
Bağlı YouTube kanalının yayın planlama/yayın hattı, desteklenen analytics ve zamanlama. Video hazır olmadan yayın DONE sayılmaz. Yayın sonucu post/read-back ile doğrulanır.

### YouTube Studio Browser Context Profile
Kendi kanalının Studio ekranlarını tarayıcı üzerinden kontrol etmek için yardımcı oturum. Profil oluşturulmuş olması tek başına `verified_connected` değildir; en az bir başarılı Studio read/run ile doğrulanır.

### Gemini
Otomatik planner/research fallback ve ikinci analiz. Çıktı kanıt yerine geçmez; kaynak/provenance korunur.

### Grok
Red-team, karşı tez, risk ve hata avı. API 403/quota gibi kendi kanal sorunları başka planları bloklamaz; uygun olduğunda normal Grok chat/file desk kullanılabilir.

### GitHub
Kod, CI, state, görevler ve teknik sistem için kanonik çalışma alanı. Canlı GitHub durumu eski mail/rapordan üstündür.

### Gmail
Yeni operasyonel sinyal, approval/account/integration sorunları. Mail canlı servis durumunun yerine geçmez.

### Google Drive
Üretim artefact'ları ve paylaşılan dosya depolama. Dosya varlığı içerik/kalite doğrulaması sayılmaz.

### Shopify + Gumroad
Commerce kanalları. Ödeme/kimlik/vergi gibi riskli ayarlar kullanıcı kapısıdır. Taslak ürün ve dosya eşleşmesi read-back ile doğrulanır.

### SEO/Marketing araçları
Ahrefs, Semrush, Ubersuggest, GSC Wizard, Windsor.ai/Supermetrics gibi bağlı araçlar talep, keyword, trafik ve performans için kullanılabilir; yalnız gerçekten bağlı/veri döndüren kaynaklar `verified` kabul edilir.

## 3. Güven ve doğrulama hiyerarşisi

1. Canlı birincil/resmi servis veya bağlı hesap verisi
2. Resmi dokümantasyon / resmi kanal / resmi filing
3. Güvenilir veri sağlayıcı / analytics connector
4. Güvenilir haber / bağımsız doğrulama
5. Creator/topluluk/arama sonucu keşif sinyali

Bir alt katman, üst katman mevcutken onu geçersiz kılamaz. Aynı iddiayı kopyalayan siteler bağımsız doğrulama sayılmaz.

## 4. Plan bazlı görev dağılımı

### Bilgi Kütüphanesi
Merkezi source catalog + learning ledger + dedup katmanı.
Akış: mevcut katalog → açık bilgi açığı → Google/TinyFish/bağlı araç keşfi → birincil doğrulama → canonical URL/tool/source_id dedup → güven sınırı ile kayıt.
Google ve YouTube ayrı kaynak sınıfları olarak eklenir.

### Video / Shorts
Akış:
1. Google/TinyFish ile konu ve kaynak keşfi
2. YouTube + vidIQ ile rakip/format/trend taraması
3. Metricool/YouTube kanal verisiyle kendi performans sinyali
4. Telif/orijinallik/monetizasyon ve kaynak doğrulaması
5. Free-first üretim hattı
6. Ses/altyazı/9:16/decode/preflight QC
7. Metricool veya doğrulanmış yetkili upload hattı
8. Yayın read-back
9. 24-48 saatlik analytics öğrenmesi ve sonraki teste aktarım

Google/YouTube/vidIQ aynı soruyu üç kez bağımsız araştırmaz; roller birbirini tamamlar.

### Shopify / Commerce
Akış: Google/SEO keşfi → talep/rakip/fiyat doğrulama → ürün/dijital asset hazırlığı → Shopify/Gumroad taslak → dosya/teslimat doğrulama → ödeme hazırsa kontrollü yayın/satış ölçümü.
Ödeme onayı yoksa mağaza hazırlığı sürer ama canlı ödeme başarılı gibi raporlanmaz.

### Sistem Geliştirmeleri
Akış: canlı state/CI → sorun kanıtı → Google/resmi docs/TinyFish ile çözüm keşfi → resmi teknik kaynak → küçük güvenli delta → test/CI/read-back → state güncelleme.
Google araması keşif, GitHub/servis durumu kanıt katmanıdır.

### Finans
Google haber/kaynak keşfinde kullanılabilir. YouTube yalnız resmi kurum/şirket kanalı veya görüş/öğrenme kaynağı olarak kullanılır. Creator videosu tek başına fiyat, bilanço, makro veya proje gerçeği sayılmaz.

### Email Monitor
Yeni maili konusuna göre ilgili plana yönlendirir; mail sinyalini canlı GitHub/Shopify/YouTube/servis durumuyla doğrular. Secret/token/password/2FA kodu kopyalanmaz.

## 5. Kalıcı durum değişiklikleri

Uygulama aşamasında yalnız gerekli küçük deltalar yapılacak:
- `knowledge/source_catalog.json`: Google Search, YouTube resmi kaynakları, vidIQ, Metricool ve doğrulanmış browser-profile kaynak türleri/durumları
- `tasks/active.json`: CORE-01/03/04/05 için daha ayrıntılı lead/backups/worker rol notları
- `state/now.json`: yalnız runtime ile doğrulanan bağlantı/sağlık durumları; browser profile `setup` ile `verified` ayrımı
- Gerekirse mevcut research/router dokümanı veya görev yönlendirme dosyası: dedup ve kaynak hiyerarşisi
- Aktif otomasyon promptları: aynı plan rolleri ve Google/YouTube kaynak kullanımı

PayoutLens dosyaları, kapsamı veya görevleri değiştirilmez.

## 6. Otomasyon güncelleme ilkeleri

Aktif saatlik planlar birbirini tekrar etmeyecek şekilde ayrılır:
- Bilgi Kütüphanesi: kaynak keşfi + dedup + reusable öğrenme
- Finans: yalnız finans/makro/kripto delta
- Video/Shopify/Sistem: üç alt kuyruk; öncelik açık işe ve gerçek blockera göre
- Email Monitor: yeni operasyonel sinyal yönlendirme

Her otomasyon önce ortak state/katalogu okur, aynı işi zaten yapan başka plan varsa duplicate iş başlatmaz.

## 7. Güvenlik ve maliyet

- Free-first yaklaşım korunur.
- Gereksiz API/ücretli üretim çağrısı yok.
- Login/2FA/payment/legal/sensitive permission/irreversible action kullanıcı kapısıdır.
- Browser profile ve vault sırları repo/loga yazılmaz.
- Google/YouTube login oturumu yalnız TinyFish profilinde saklanır; profil adı veya ID gerekiyorsa sır olmayan metadata olarak tutulabilir, session/cookie değeri tutulmaz.

## 8. Doğrulama planı

Uygulama tamamlandı sayılmadan:
1. Değiştirilen JSON dosyaları parse edilir.
2. Kaynak katalogunda canonical dedup kontrol edilir.
3. `tasks/active.json` ve `state/now.json` read-back ile doğrulanır.
4. Uygun repo test/CI çalıştırılır; yalnız docs/state değişikliği ise en az JSON/schema/desk-context kontrolleri uygulanır.
5. Otomasyon promptları update sonrası read-back ile kontrol edilir.
6. YouTube Studio Browser Context Profile ancak gerçek Studio read/run başarılı olursa `verified` yapılır.
7. Metricool YouTube bağlantısı canlı brand settings/analytics/yayın aracı ile doğrulanmış durumda tutulur.
8. Doğrudan YouTube OAuth `invalid_grant` kaydı, Metricool alternatif yayın hattı çalışsa bile ayrı blocker olarak yanlışlıkla silinmez; yalnız gerçek OAuth testi düzelirse kapatılır.

## 9. Non-goals

- Yeni ücretli servis satın almak
- PayoutLens'i değiştirmek
- Opera Connector'ı zorunlu hale getirmek
- Google arama sonucunu otomatik gerçek kabul etmek
- YouTube'da telifli videoları izinsiz yeniden kullanmak
- Direct YouTube OAuth blocker'ını kanıtsız çözülmüş göstermek

## 10. Beklenen sonuç

Tekrarsız, kaynak güven seviyesi belirli, Google + YouTube destekli bir araştırma/üretim sistemi; kendi YouTube kanalında Metricool/Studio/vidIQ rollerinin ayrıldığı; teknik ve commerce işlerinin aynı ortak bilgi katmanından yararlandığı; bağlantı hatalarının diğer planları gereksiz yere durdurmadığı bir görev dağılımı.
