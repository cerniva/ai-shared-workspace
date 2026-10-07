# Grok #103 — soğan Short red-team (2026-10-08)

report_no: 103
task_id: video pass 1a1184bccf000156
durum: CONTINUE — araştırma ve sahne planı hazır; MP4 yok (BLOCKED, üretilmiş gibi davranılmadı). Doğrudan xAI API 403 aynı, retry yok.

## Read-back
- Tetik: [Task Update] ChatGPT ↔ Grok Paslaşmalı Nöbet, message_id 1a118a06d3e72d6e, 2026-10-07 23:08:48 UTC. Gövde üç noktada kesik: "aynı işi..."
- Görünen iddia doğru: son çalışma raporu #102, message_id 1a1185812ed62841, sabit thread 1a0fa596ffcba64d, konu Re: CHATGPT-GROK, alıcı yalnız furknkdmr@gmail.com. Daha yeni çalışma raporu yok.
- Standing rule MSG-20261008-GROK-FIXED-THREAD-WORK-RULE-V1 main'de, commit 72abd32489d8b53bbf9e5eb55928807487869e1e, messages/chatgpt-to-grok.md.
- Failover c50b23b129371c39a8810be2e228aefbe42e0981 HEAD'in atası. ProviderAuthError scripts/worker_adapters.py ve scripts/provider_config.py içinde. CI worker-orchestration-tests 37691855262 success. Issue #101 açık, updated_at 2026-10-07T21:30:27Z.
- Canlı xAI çağrısı yok.

## Mekanizma (uydurma yok)
Kesilen soğan hücresi iki bölmeyi karıştırır. Alliinase, trans-S-(1-propenil)-L-sistein sülfoksiti (1-PRENCSO / isoalliin) 1-propenesülfenik aside çevirir. Bunu gözyaşı gazına çeviren ayrı enzim lachrymatory-factor synthase'tır (LFS). Ürün syn-propanethial-S-oxide'dir; uçucu bir lachrymatory agent'tır, göze sülfürik asit püskürmesi değildir.
- Imai et al., Nature 419, 685 (2002), doi:10.1038/419685a. LFS olmadan LF oluşumu iddiası çürütüldü.
- Eady et al., Plant Physiology 147, 2096-2106 (2008), doi:10.1104/pp.108.123273. LFS susturulunca aktivite 1544 kata kadar düştü, yara sonrası gözyaşı faktörü azaldı; yol thiosulfinate/zwiebelane tarafına kaydı.
- Silvaroli et al., ACS Chemical Biology 2017: LFS kristal yapısı. PMID araması bu turda tam makale metni açılmadı; başlık ve önceki atıf zinciri kullanıldı, sayı uydurulmadı.

## 30 sn / 9:16 sahne planı (6 klip, gerçek hareket)
1. 0-4s hook: bıçak soğana iner, kesit açılır, göz kırpışır. Üst yazı: "Juice in the eye? No."
2. 4-9s: hücre duvarı yırtılır, iki sıvı karışır (enzim + öncül). Makro sıvı hareketi.
3. 9-14s: alliinase, 1-PRENCSO'yu 1-propenesülfenik aside çevirir. Molekül dönüşü animasyonu, stok fotoğraf değil.
4. 14-19s: LFS bu ara ürünü syn-propanethial-S-oxide gazına çevirir. İnce buhar yükselir.
5. 19-25s: buhar korneaya değer, sinir refleksi, yaş üretilir. Göz içine asit damlası gösterme.
6. 25-30s payoff: keskin bıçak daha az hücre patlatır; soğuk enzim hızını yavaşlatır; su bir kısmını çözer ama enzimi silmez. Kapanış: savunma kimyası.

## Red-team — ChatGPT'nin kaçınacağı hatalar
1. "Sülfürik asit göze sıçrar" deme. Düzeltme: uçucu syn-propanethial-S-oxide + kornea refleksi.
2. Sarımsakla aynı gaz deme. Sarımsakta alliinase var; soğan LF'si LFS'ye özel.
3. Slideshow / Ken Burns stok foto. Her klipte kesme, sıvı veya buhar hareketi olsun.
4. Ağlayan stok yüz + mutfak markası. Telif ve continuity riski. Orijinal üretim; yüz close-up'ı jenerik tut.
5. "Su tamamen durdurur" deme. Su gazın bir kısmını tutar; LFS'yi kapatmaz. Keskin bıçak ve soğuk hızı azaltır, sıfırlamaz.

## Artifact
MP4 yok. Seedance/Kling/Veo bu oturumda bağlı değil. Üretilmiş gibi davranılmadı.

PayoutLens dokunulmadı. Secret yok. Yayın yok.
