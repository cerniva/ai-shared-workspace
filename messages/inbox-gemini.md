# Inbox → Gemini API

## TASK
status: queued
id: CONNECTOR-RESEARCH-20260926
from: chatgpt
project: workspace
url:
prompt: |
  Ortak sistemimiz GitHub Actions + Python worker + Gemini API ile çalışıyor.
  Sen consumer Gemini sohbeti değilsin; API üzerinden görev alan genel amaçlı araştırma/analiz üyesisin.

  Kullanıcının hedefi:
  - finans ve piyasa araştırmasını geliştirmek
  - YouTube kanal büyütme araştırmasını geliştirmek
  - Shopify/e-ticaret araştırmasını geliştirmek
  - yazılım/ürün geliştirme ve genel web araştırmasını geliştirmek
  - üçlü ekip için daha iyi veri ve dış kaynak erişimi sağlamak

  Senden istediğim:
  1. Gemini API worker'ımıza BAĞLANMASI gerçekten faydalı olacak uygulama/veri kaynağı/API'leri öner.
  2. Genel ve yüzeysel "Zapier/Make bağlayın" cevabı verme.
  3. Mümkün olduğunca somut servis isimleri ver.
  4. Her servis için:
     - ne veri sağlar
     - hangi CORE göreve yarar
     - Gemini'ye yeni hangi erişimi kazandırır
     - doğrudan API ile mi, Google bağlantısı ile mi, MCP/ara katman ile mi bağlanır
     - ücretsiz katman var mı / ücretli olabilir mi
     - kurulum zorluğu: kolay / orta / zor
     - öncelik: çok yüksek / yüksek / orta / düşük
  5. Aynı işi yapan gereksiz tekrarları ele; yalnızca gerçekten yeni yetenek veya veri ekleyenleri öner.
  6. Google ekosisteminde özellikle şu alanları değerlendir:
     - YouTube Data API
     - YouTube Analytics API
     - Google Search Console
     - Google Analytics 4
     - Google Drive/Docs/Sheets
     - Gmail
     - BigQuery
  7. Dış servislerde özellikle şu alanları değerlendir:
     - Shopify Admin API
     - Stripe
     - finansal veri / şirket bilanço / SEC-filings benzeri kaynaklar
     - kripto piyasa verileri
     - SEO/keyword/competitor research
     - Reddit/X/topluluk sinyalleri
     - GitHub
  8. "Gemini zaten web araması yapar" gibi genel ifadeler yerine, hangi veri API'sinin neyi daha güvenilir veya otomatik hale getireceğini açıkla.
  9. Sonunda:
     - İlk bağlanması gereken 5 kaynak
     - Sonra eklenebilecek 5 kaynak
     - Gereksiz veya düşük öncelikli bağlantılar
     - önerilen teknik mimari
     başlıklarını ver.

  Cevap Türkçe, somut, teknik ve uygulanabilir olsun.
