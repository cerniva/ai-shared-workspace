# Sistem denetimi — 26 Eylül 2026

## Doğrulanan durum

- Repo public. GitHub Actions'daki Gemini köprüsü önce başarılı YouTube testi vermiş, son Shopify testlerinde 503/429 almış. Son 429 yanıtında proje/model için ücretsiz 20 istek kotası görülüyor.
- Shopify bağlayıcısı son sağlık kontrolünde mağazaya erişmiş ve 9 ürünü özetlemiş; bu, ürünlerin satışa hazır olduğu anlamına gelmez.
- YouTube Data API bağlayıcısı önceki YTTEST2 denemesinde çalışmış. YouTube Analytics OAuth üçlüsünün canlı rapor testi henüz doğrulanmadı.
- Grok için çalışan otomatik GitHub Action yok. Mesaj dosyaları handoff sağlar; zamanlanmış ajan çalışması sağlamaz.

## Uygulanan düzeltmeler

1. Tek Gemini worker bırakıldı. Kullanılmayan ikinci workflow ve eski worker kaldırıldı.
2. Gemini 429/503 veya boş yanıt verdiğinde görev tamamlandı sayılmıyor. Kuyruk korunuyor; saatlik zamanlanmış Action yeniden deniyor. Günlük kota 429'u hızlıca dört kez denemiyor.
3. Gemini'nin bağlantı talebi ancak mevcut araçlarla çözülemeyen zorunlu insan işlemi için isteniyor.
4. Netlify yalnızca site HTML'ini yayımlıyor. Repo dosyaları deploy paketine dahil edilmiyor.
5. Public repoda Shopify/YouTube Analytics özel veri görevleri hem bağlayıcı zenginleştirmesinde hem Gemini worker'da bloke ediliyor. Bağlayıcı sağlık dosyası izleme dışına çıkarıldı.
6. YouTube Data API anahtarı URL yerine HTTP header'ı ile taşınıyor.
7. Görev bağlamı küçültüldü; Gemini kod incelemesine yalnızca açıkça seçilen public kaynak dosyaları eklenebiliyor.
8. Üçlü görüş kuralları hızlı yol ile hizalandı. CORE başlıkları gerçek zamanlı çalışan otomasyon gibi gösterilmiyor.
9. Mevcut depodaki metin dosyalarında yaygın API anahtarı/özel anahtar biçimleri tarandı; eşleşme bulunmadı. Geçmiş commit'ler bu taramanın kapsamı dışındadır.

## Kalan sınırlar

- Gemini kotası harici servis sınırıdır. Kota açılmadan Gemini cevabı alınamaz; kuyruk otomatik denenir.
- Özel Shopify/Analytics analizini Gemini ile güvenle kalıcılaştırmak için public repo dışında özel bir yanıt alanı gerekir. Public repoda bu işlem bilerek bloke edilmiştir.
- YouTube Analytics OAuth canlı testi üç secret ve kanal izni tamamlandıktan sonra yapılabilir.
- Bu repo tek başına sürekli finans/Shopify/içerik işleri çalıştırmaz. Bunlar takip başlığıdır; gerçek otomasyon ayrı tetikleyici ve çalışma tanımı gerektirir.
