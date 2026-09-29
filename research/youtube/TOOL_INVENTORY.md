# Shorts araç envanteri — 2026-09-29

Kaynak: kullanıcı envanter metni + canlı connector/GitHub doğrulamaları.
Geçmiş kullanım ≠ şu an bağlı.

## A. Eski otomasyonda kayıtla doğrulanan

| Araç | Eski kullanım | Güncel durum |
|---|---|---|
| HeyGen | İlk Short 5 sahne, 9:16, 720p grafik | Geçmiş kullanım kaydı var; güncel üretim erişimi bu tur doğrulanmadı. |
| ElevenLabs | Hız 1 / stab 0.5 / sim 0.75 (HeyGen içi) | Ayrı connector erişimi doğrulanmadı. |
| Metricool | Kanal bağlantısı | **BAĞLI DEĞİL / yayın fallback'i kullanılamaz:** 2026-09-29 canlı `getBrandSettings` kontrolünde brand/blog `7082876` için hiçbir sosyal ağ bağlı görünmedi. Geçmişte listelenmiş olması güncel bağlantı kanıtı değildir. YouTube ağı yeniden bağlanıp canlı read-back başarılı olmadan Metricool yayın yolu yeşil sayılmayacak. |
| YouTube | Yayın platformu | GitHub upload hattı mevcut; doğrudan OAuth `invalid_grant` nedeniyle yayın yetkisi bloklu. Üretim/preflight başarısı yayın başarısı değildir. |
| vidIQ | Örnek analiz | Araştırma/analytics için kullanılabilir olduğunda ayrı doğrulanır; yayın hattı değildir. |
| Airtable Cerno Growth Lab | Kayıt defteri | Eski kayıt; ortak GitHub `research/youtube/` + knowledge/state tercih edilir. |

İlk Short geçmiş referansı: https://www.youtube.com/shorts/bWK56KLxAYk

## B. Güncel doğrulanmış üretim altyapısı

- GitHub `cerniva/ai-shared-workspace` — free-first Shorts research/render/preflight hattı.
- FFmpeg + eSpeak NG — kredi gerektirmeyen yerel render/TTS temeli.
- Pexels/Pixabay/Openverse sınıfı free-media kaynakları — dosya bazlı provenance/lisans doğrulaması şart.
- `shorts_preflight.py` — exact MP4 teknik kalite kapısı; publish için ready/read-back gerekir.
- Metricool — connector görünür olsa da sosyal ağ bağlantısı şu anda yok; yayın fallback'i **aktif değil**.

## C. Alternatifler

InVideo, Runway, Synthesia, Viewmax/Everygen, Visla, Adobe, Canva video ve benzeri üretim yolları yalnız erişim/maliyet/kalite açısından free-first hat yetersiz kalırsa değerlendirilir. Bağlı/çalışır oldukları canlı doğrulama olmadan varsayılmaz.

## D. Araştırma kaynakları — erişim

Açık web ve GitHub araştırması kullanılabilir. YouTube Studio/owned analytics/Metricool gibi hesap-bağımlı kaynaklar her kullanım öncesi canlı erişim doğrulaması gerektirir.

Örnek Shorts teknik dersi (kopya yok): Z3Okx3RXhEU, oT1M2QORfUU, ls1gW-EHx80.
