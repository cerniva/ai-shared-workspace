# Shopify Ürün Adayları ve Doğrulama

Aday bulunması yayın kararı değildir. Her satırda talep, rekabet, dosya/tedarik, maliyet ve haklar ayrı doğrulanır. Özel müşteri verisi burada tutulmaz.

## 2026-09-27 — Kafe/restoran reçete maliyeti ve yenilebilir verim şablonu

- **Mevcut durum:** Food Cost türü dijital ürünün taslak olduğu ortak görev kaydında belirtiliyor. Bu kayıtta ürünün dosya içeriği veya canlı satışa hazır oluşu doğrulanmadı.
- **Rakip/arz kanıtı:** Someka'nın [Google Sheets şablonu](https://www.someka.net/products/food-cost-google-sheets-template/) hammadde listesi, reçete maliyeti, porsiyon maliyeti ve satış özeti sunuyor; [Excel sürümü](https://www.someka.net/products/food-cost-excel-template/) de var (27 Eylül 2026 kontrolü). Bunlar ihtiyacın piyasada tanımlandığını ve güçlü bir alternatif bulunduğunu gösterir; satış hacmi veya bizim ürüne talep kanıtı değildir.
- **Olası dar açı/hipotez:** Küçük kafeler için reçete maliyetini yenilebilir verim/fire, porsiyon ve güncellenen alış fiyatıyla birlikte tek örnekte gösteren özgün araç. Bu farkın gerçekten arandığı henüz doğrulanmadı.
- **Tedarik/teslim:** Dijital dosya varsayımıyla fiziksel stok ve kargo yok. Shopify [dijital ürün yardımına](https://help.shopify.com/en/manual/products/digital-service-product/selling-services-or-digital-products) göre teslim uygulaması ve test siparişi gerekir; mevcut dosya ve teslim akışı bu kontrolde test edilmedi.
- **Maliyet/net marj:** Dosya geliştirme süresi, ödeme/Shopify ücretleri, vergi ve iade etkisi bilinmiyor; fiyat veya net marj hesaplanmadı.
- **Haklar:** Rakip şablonların formül/tasarım/metni kopyalanmayacak. Özgün dosya ve görsel hakları incelenmeli.
- **Karar:** Araştırma adayı; yayın yok. Sonraki kanıt: hedef müşteri arama/yorum sinyali, mevcut taslak dosyanın özgün içeriği ve gerçek teslim testi. Başarı ölçütü: nitelikli geri bildirimde verim/fire özelliğine açık ihtiyaç; sonrasında gerçek dış trafik, sepet ve sipariş.


## 2026-09-27 08:05 TR — Aday farkı: yenilebilir verim boşluğu

- **Durum:** `ham` → `inceleniyor`. Yayın kararı yok.
- **Yeni kanıt:** [RestaurantOwner reçete maliyet şablonu](https://www.restaurantowner.com/public/DOWNLOAD-Menu-Recipe-Cost-Spreadsheet-Template.cfm) satın alma birimini reçete birimine dönüştürüyor, güncel hammadde fiyatıyla reçete maliyetini yeniliyor ve porsiyon/alt reçete akışı sunuyor; kendi açıklamasında ürünün bir yield/verim hesaplayıcısı olmadığını belirtiyor. [Restaurant365](https://www.restaurant365.com/blog/calculating-food-costs-how-to-nail-down-this-ops-cost-enigma/) ise güncel olmayan fiyatlar ve manuel veri girişinin maliyet hesabını bozabileceğini vurguluyor.
- **Karar farkı:** “Sadece reçete maliyeti” yeterince farklı değil. Aday ancak **satın alma birimi → yenilebilir miktar/fire → porsiyon maliyeti → hedef satış fiyatı** akışını özgün ve kolay kullanımlı biçimde doğrulayabilirse ilerletilecek.
- **Sınırlama:** Bunlar rakip ve ticari sektör kaynaklarıdır; satış hacmi veya hedef müşterinin ödeme isteği değildir. Mevcut taslak dosyanın bu özellikleri içerip içermediği bu turda okunmadı.
- **Uygulama/ölçüm:** Aday havuzu daraltıldı; fiyat/yayın yapılmadı. Sonraki tetikleyici, taslak dosya içeriğinin okunabilmesi veya küçük kafe/restoran kullanıcılarından yenilebilir verim/fire ihtiyacına dair nitelikli geri bildirim gelmesi. Yeniden kontrol: dosya erişimi oluştuğunda; en geç 2026-10-04 haftalık aday incelemesinde.


## 2026-09-27 09:00 TR — Resmi verim kaynağı bulundu; ürün kapsamı netleşti

- **Yeni kanıt:** USDA Food Buying Guide, AP (satın alınan) ile EP (yenilebilir/hazır) miktarını ayırıyor ve ürün biçimine göre verim hesap örnekleri veriyor. USDA ARS ayrıca et ve kanatlı için pişirme verimi tabloları yayımlıyor.
- **Karar farkı:** Ürün yalnız manuel fire yüzdesi alanı değil, **kaynak etiketli referans verim + kullanıcı ölçümüyle geçersiz kılma** yapısı sunmalı. Böylece başlangıç kolaylaşır fakat ortalama ABD verisi Türkiye'deki tedarikçi/ürün/mutfak tekniği için kesin doğru gibi sunulmaz.
- **Sınırlama:** Resmi kaynak, hedef müşterinin ödeme isteğini veya Türkiye pazar talebini kanıtlamaz. Mevcut taslak dosyanın formülleri ve lisansı hâlâ okunmadı.
- **Mağaza ölçümü:** 24–27 Eylül hunisinde yeni sepet, checkout, sipariş veya satış sinyali oluşmadı; küçük örneklem ve parola/ödeme engeli devam ediyor.
- **Sonraki tetikleyici:** Taslak dosya erişildiğinde AP→EP formülünü, birim dönüşümünü, kullanıcı override alanını ve kaynak notunu doğrula. Talep doğrulanmadan fiyat/yayın yok.
