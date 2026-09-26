# Meta ekibi: bağlantı durumu ve tarayıcı yolu

## Şu an hazırlanan

Meta Model API (Muse Spark) mevcut `scripts/worker_adapters.py` arayüzüne `meta` sağlayıcısı olarak bağlanır. Kuyruktaki araştırma/analiz işini alıp standart kanıt biçiminde döndürür. `META_MODEL_API_KEY` yoksa istek gönderilmez; anahtar GitHub Actions secret olarak eklenir, repoya yazılmaz. Sağlayıcı failover sıralamasının sonundadır.

Bu API bağlantısı kullanıcının Meta AI sohbet oturumu veya Muse kişisel ajanı değildir. Bağlantı anahtarı ve canlı uçtan uca deneme yapılana kadar Meta'nın çalıştığı iddia edilmez.

## Site işlemleri için sonraki teknik katman

Meta Model API'nin `computer` aracı, ekran görüntüsüne karşılık eylem önerir. Tıklamayı Meta sunucusu gerçekleştirmez. Bunun için ayrı, sürekli çalışan bir tarayıcı sürücüsü gerekir:

1. İzole Playwright tarayıcı ortamı; ekran görüntüsü ve eylem yürütme döngüsü.
2. Repo kuyruğundan tek iş alma; izin verilen alan adları ve eylem türleri için `scripts/policy_gate.py` denetimi.
3. Her adım için eylem, URL ve sonuç kaydı; adım sınırı, zaman aşımı ve hata durumunda durma.
4. Hesap girişi, gizli bilgiler, ödeme, yayınlama ve geri döndürülemez işlemleri mevcut politika ile sınırlandırma.
5. Shopify gibi desteklenen servislerde mümkünse resmi API/connector yolunu kullanma; tarayıcı sürücüsünü uygun görevlerde seçme.
6. Test ortamında önce yalnızca herkese açık sayfada gezinti; ardından kullanıcı oturumu ve erişim altyapısı varsa izinli işlemler.

Mevcut `scripts/browser_executor.py` yalnızca HTTP GET kanıtı üretir; tıklama yapmaz. API anahtarı eklemek tek başına tarayıcı otomasyonunu etkinleştirmez.

Resmi referanslar:
- https://dev.meta.ai/docs/quickstart
- https://dev.meta.ai/docs/computer-use
- https://dev.meta.ai/docs/tool-calling
