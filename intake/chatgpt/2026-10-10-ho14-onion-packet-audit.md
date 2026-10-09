# HO-20261010-14 — Soğan Shorts paket taraması / taslak (2026-10-10)

id: HO-20261010-14
from: chatgpt
to: grok
intent: evidence+handoff
status: blocked_missing_approved_onion_packet

## main üzerinde bulunan doğrulanmış JSON yolları
1. `knowledge/shorts/packets/SHORT-RES-001.json` — Türkiye'de AI mesajları; soğan konusu değil, `free_render_requested` ve `media_queries` yok. Soğan için kullanılamaz.
2. `tests/fixtures/shorts_real_smoke_ice_float.json` — İngilizce buzun yüzmesi testi, `free_render_requested=true`, `media_queries` mevcut; soğan konusu değil ve test fixture'ı. Soğan için kullanılamaz.
Arama: GitHub default-branch code search `target_seconds`, `media_queries`; ilgili sonuçlar yukarıdaki iki JSON. **Bu bir repository tree'nin eksiksiz listesi değildir**; başka JSON olasılığını kesin dışlamaz. Hiçbir doğrulanmış soğan packet JSON yolu bulunmadı.

## Gate ve ücretsiz hareketli görüntü koşulları
Kaynak: `scripts/shorts_research.py:gate_packet` ve `scripts/shorts_free_pipeline.py:prepare_render_bundle`.
Gate için zorunlu: topic, why_selected, trend_or_evergreen, hook, target_seconds, en az 2 kaynak, unique_angle, script_beats, visual_plan, audio_plan, title, hashtags ve bütün prepublish_checklist true. `free_render_requested=true` ise language, content_type, narration_text, geçerli media_queries şart. Duplicate/hook kontrolleri ayrıca geçilmeli.
Gate geçmek **medya lisansı veya gerçek MP4'ü doğrulamaz**. Pipeline arama sonuçlarından gerçek video indirir, `ffprobe` ile doğrular; resim fallback'i kapalı. Pexels/Pixabay sonuçları, erişim/ücretsiz lisans ve kaynak kanıtı ayrıca kontrol edilmeli. Onay olmadan checklist `rights_ok`, `facts_verified` ve `publishable_quality_planned` true yazılamaz.

## Soğan paketi taslağı — BİLEREK gate'e verilmemeli / workflow tetiklenmemeli
Aşağıdaki taslak **onaylı packet JSON değildir**; görev tanımıdır:
- topic: Soğan keserken neden gözlerimiz yaşar?
- target_seconds: 30; language: tr; content_type: short_fact; free_render_requested: true
- hook: "Soğanı kesince gözlerin neden yanıyor?"
- original story beats: 0–3 kesme/kanca; 3–10 hücrelerin parçalanması; 10–18 uçucu tahriş edici maddenin göze ulaşması; 18–25 gözyaşı refleksi; 25–30 merak uyandıran kapanış
- visual_plan: gerçek hareketli yakın plan soğan kesme, soğan hücreleri için özgün basit animasyon veya lisanslı hareketli çekim, göz sulanması (haklar kontrol edilmeli)
- media_queries: ["onion chopping close up vertical video", "cutting onion crying eyes vertical video", "onion sliced cutting board macro video"] (yalnız sorgu; hiçbir klip bulunmuş/lisanslanmış sayılmaz)
- narration_text: özgün Türkçe 30 saniyelik seslendirme metni hazırlanmalı ve süre/ses kalitesi doğrulanmalı
- sources: en az iki **doğrulanmış** birincil/kurumsal kaynak URL'si gerekli; henüz eklenmedi
- prepublish_checklist: hiçbir doğrulanmamış alan true işaretlenmeyecek; factual, copyright, 9:16, original hook/storyboard, moving footage, voice, subtitles ve rights gözden geçirilmeli
- quality: eSpeak-ng sentetik ses, Furkan'ın doğal ses beklentisini karşılamayabilir; gerçek MP4 bağımsız QC olmadan publishable değildir

## Eksikler ve Grok için en küçük sonraki adım
1. Resmî/kurumsal en az iki soğan-gözyaşı mekanizması kaynağı URL + doğrulama tarihi.
2. Özgün 30s Türkçe anlatım, storyboard, kanca ve onay; duplicate kontrolü.
3. Pexels/Pixabay'dan gerçek hareketli klip URL/provider_asset_id + lisans + indirilebilirlik + dikey kırpma doğrulaması; ücretli/iStock varlıklar dışarıda.
4. `rights_ok`, `facts_verified` vb. checklist değerlerini kanıtla; onaylı JSON'u `knowledge/shorts/packets/` altında yeni adla oluştur; `python3 scripts/shorts_research.py gate --packet <GERCEK_DOSYA>` çalıştır.
5. Sadece gate temizse ve ücretsiz medya bulunursa `shorts-free-build.yml` tetikle; artefakt MP4'ü ve preflight'ı doğrula. Satın alma/yayın yok.

Proof: `main` kaynak dosyaları GitHub connector üzerinden okundu. Yerel gate komutu çalıştırılmadı; gate geçti iddiası yok. Bu taslak bir workflow input'u değildir. PayoutLens kapsam dışı.
