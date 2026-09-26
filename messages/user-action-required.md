# User Action Required

Gemini veya ekip bir insan işlemi gerektiğinde buraya kayıt bırakır.

---
id: ACTION-20260926-030500-youtube-data-api
source: chatgpt
task: CORE-03
created_at: 2026-09-26T03:05:00+03:00
status: open
---

## BAĞLANTI GEREKİYOR
- Servis / uygulama: YouTube Data API v3
- Neden gerekli: Ortak worker'ın public video/kanal metadata, istatistik, arama ve yorum verisini yapılandırılmış olarak çekmesi için.
- Bağlantı türü: Google Cloud API + GitHub Secret
- Kullanıcıdan gereken işlem: YouTube Data API v3'ü etkinleştir, API key oluştur, GitHub secret'a ekle.
- Gerekli secret / izin adı: YOUTUBE_API_KEY
- Ücretsiz / ücretli: Kota bazlı; standart kullanım için ücretsiz kota mevcut.
- Öncelik: çok yüksek
- Geçici alternatif: Gemini doğrudan YouTube URL'sini analiz edebilir; ancak yapılandırılmış Data API verisi eksik kalır.
