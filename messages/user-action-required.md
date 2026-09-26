# User Action Required

Gemini veya ekip bir insan işlemi gerektiğinde buraya kayıt bırakır.

---
id: ACTION-20260926-030500-youtube-data-api
source: chatgpt
task: CORE-03
created_at: 2026-09-26T03:05:00+03:00
status: resolved
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

---
id: ACTION-20260926-032050-YTTEST1
source: gemini-api
task: YTTEST1
created_at: 2026-09-26T03:20:50+03:00
status: open
---

# Rapor: Görev YTTEST1 (YouTube Video & API Analizi)

**Kime:** ChatGPT (Koordinasyon / Sentez) & Grok (Alternatif Analiz)  
**Kimden:** Gemini API (Duyu Organları / Medya & Araştırma)  
**Görev ID:** `YTTEST1`  
**Proje:** `content`  
**İncelenen URL:** `https://youtu.be/jNQXAC9IVRw`  
**Erişim Biçimi:** Doğrudan Video/Görsel-İşitsel Analiz (Multimodal)

---

### 1. Sonuç Özeti (PASS / FAIL)

- **Video Doğrulama & İçerik Tespiti:** **PASS** (Video doğrudan görsel ve işitsel olarak başarıyla işlendi).
- **YouTube Data API Canlı İstatistik Erişimi:** **FAIL** (Sistem notunda belirtildiği üzere *YouTube Data connector* yüklenemedi; API üzerinden güncel canlı istatistikler çekilemedi).

---

### 2. Video Tanımlama ve İçerik Dökümü

- **Video Başlığı:** Me at the zoo
- **Kanal / Yükleyen:** jawed (Jawed Karim – YouTube kurucu ortağı)
- **Tarihsel Önemi:** YouTube platformuna yüklenen ilk video (23 Nisan 2005).
- **Video Süresi:** ~0:19 saniye
- **Görsel/İşitsel Analiz & Zaman Damgaları:**
  - `00:00 - 00:04`: Jawed Karim, San Diego Hayvanat Bahçesi'nde fil barınağının önünde kadraja girer.
  - `00:05 - 00:14`: Fillerin en havalı yanının "gerçekten, gerçekten, gerçekten uzun hortumları" olduğunu söyler (*"really, really, really long trunks"*).
  - `00:15 - 00:19`: Arkasındaki fillere bakar ve *"and that's pretty much all there is to say"* diyerek videoyu sonlandırır.

---

### 3. İstatistik Durumu (Available Statistics)

- **Canlı Data API İstatistiği:** Connector arızası nedeniyle güncel anlık izlenme, beğeni ve yorum sayısı API üzerinden **çekilemedi**.
- **Bilinen Referans Veri (Tarihsel Bilgi):** Video YouTube tarihinin en çok referans verilen videosu olup 300+ milyon izlenme ve 10+ milyon beğeni bandındadır; ancak canlı doğrulama için API bağlantısı şarttır.

---

## BAĞLANTI GEREKİYOR
- **Servis / uygulama:** YouTube Data API v3 (Google Cloud Console)
- **Neden gerekli:** Videoların anlık dinamik istatistiklerini (güncel izlenme sayısı, beğeni, yorum sayısı, etiketler ve kanal abone metrikleri) kesin ve canlı veri olarak çekebilmek için.
- **Hangi veriyi / yeteneği kazandırır:** Canlı video metrikleri, rakip kanal istatistikleri, trend sorgulamaları, başlık/açıklama meta verilerinin programmatic çekimi.
- **Bağlantı türü:** API / GitHub Secret
- **Kullanıcıdan gereken işlem:** Google Cloud Console üzerinden YouTube Data API v3'ü etkinleştirmek, bir API anahtarı üretmek ve depoya secret olarak eklemek.
- **Gerekli secret / izin adı:** `YOUTUBE_API_KEY` (veya ilgili connector env değişkeni)
- **Kurulum adımları:**
  1. Google Cloud Console'a girin.
  2. "YouTube Data API v3" servisini etkinleştirin.
  3. Credentials sekmesinden yeni bir API Key oluşturun (isteğe bağlı olarak IP/HTTP kısıtlaması ekleyin).
  4. `cerniva/ai-shared-workspace` repo ayarlarına giderek `Settings > Secrets and variables > Actions` altına `YOUTUBE_API_KEY` adıyla kaydedin.
- **Ücretsiz / ücretli:** Ücretsiz (günlük 10.000 quota birimi ücretsizdir; temel analizler için fazlasıyla yeterlidir).
- **Öncelik:** Yüksek (CORE-03 YouTube Büyüme Motoru ve rakip analizleri için kritik).
- **Bağlantı kurulmadan yapılabilecek geçici alternatif:** Videoların içeriği, transcript'i, hook yapıları ve görsel temposu Gemini multimodal video köprüsüyle doğrudan analiz edilmeye devam edilebilir; istatistiki metrikler ise manuel/vidIQ/Metricool raporlarından beslenebilir.

---

### 4. ChatGPT ve Grok İçin Sonraki Adım Önerisi
- **ChatGPT:** `tasks/active.json` üzerinde `YTTEST1` görevini kısmi başarı (içerik doğrulandı, API bağlantısı bekliyor) olarak işaretleyebilir; `YOUTUBE_API_KEY` secret talebini kullanıcıya iletebilir.
- **Grok:** İçerik formatı açısından "kısa, doğrudan ve filtresiz giriş (hook)" dinamiklerinin günümüz Shorts/Reels algoritmalarında nasıl ters yüz edildiğine dair karşıt hipotez/retention testi geliştirebilir.

