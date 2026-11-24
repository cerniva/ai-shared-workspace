# Cerno Short paketi — 2026-11-01 — Mantar yıkanmaz mı? Hangisi sünger gibi su çeker?

Durum: üretim öncesi paket. YouTube/Buffer'a yükleme yok, post yok; yayın için Furkan'ın "yayınla" onayı ve video URL'si gerekir.
Kuyruk: mutfak kuyruğu 01–14 (26 Eyl = 01) bitti, bugün 37. gün; kural gereği varsayılan mutfak hattı devam (finans/AI/clickbait'e kayma yok).
Tekrar kontrolü: önceki konular (Mbappé, uçak penceresi deliği, uçak koltuğu, JUICE, Shorts algoritma, soğan, TR AI kullanımı, taze yumurta soyma, buzdolabında ekmek, acı biber/süt, Leidenfrost tava damlası, tuzlu su kaynama, donan bal, elma kararma, patlamış mısır, bulanık buz, domates buzdolabı, sarımsak yeşerme, mor lahana) ile çakışmıyor. Repo genelinde `git grep -i "mantar|mushroom"` (main 9578e09) sonuç vermedi.
Seri bağı: "mutfak efsanesi → tartı testi" (yumurta soyma, ekmek buzdolabı, domates buzdolabı ailesi); renk serisinden bilinçli ayrılış, tek değişken = konu ailesi.
İdea havuzu: #27 Kitchen myth → test → result + #31 Food storage micro-tip + #29 One cooking mistake fixed.
Süre: ~28 sn · 9:16 · 1080x1920 · Türkçe

## Kaynaklar (doğrulandı, 2026-11-01)
1. America's Test Kitchen, "Should You Wash Mushrooms? The Definitive Answer" — https://www.americastestkitchen.com/how_tos/11827-should-you-wash-mushrooms
   - Beyaz, kremini, portobello, shiitake, istiridye ve maitake 1 dakika suya batırılıp öncesi/sonrası tartıldı: lameli (alt yüzdeki ince yapraklar) açıkta olmayanlar neredeyse hiç su tutmadı, lameli açıkta olanlar ağırlıklarının %25'ine kadar su çekti.
   - Mantarlar suyu iten hidrofobin proteinleri salgılar; açık lameller ise suyu tutar, pişirmeyi uzatır ve kızarmayı zorlaştırır.
   - Kültür mantarları çoğunlukla temizdir; temizlenecekse açık lamelliler fırça/kâğıt havluyla silinir. Doğadan toplananlar iyice yıkanmalı.
2. America's Test Kitchen, "Our Guide to Fresh Mushrooms" — https://www.americastestkitchen.com/articles/1442-our-guide-to-fresh-mushrooms
   - Lamelsiz türler yıkanabilir ama doğramadan ÖNCE; kesik yüzey suyu sünger gibi çeker. Salata kurutucu en verimli kurutma.
3. Serious Eats (J. Kenji López-Alt), "How to Clean and Prepare Mushrooms" — https://www.seriouseats.com/how-to-clean-and-chop-mushrooms
   - Akan suda yıkanıp kurutulan mantar ağırlığının yaklaşık %2'si kadar su aldı (~1,5 çay kaşığı/454 g); pişirmeye 15–30 sn ekler. Yıkama pişirmeden hemen önce yapılmalı, fazla nem buzdolabı ömrünü kısaltır.
4. The Guardian (Felicity Cloake), "Should you wash mushrooms?" (2010) — https://www.theguardian.com/lifeandstyle/wordofmouth/2010/jan/18/should-you-wash-mushrooms
   - Harold McGee testi: 252 g mantar 5 dk suda bekletildi, kurulanınca 258 g geldi (yalnızca 6 g).
İfade kuralları: "Mantar asla su çekmez" denmez (az da olsa çeker). "%25" yalnızca açık lamelli türler + 1 dk batırma koşuluyla söylenir. "Yıkamayan zehirlenir" ya da hijyen/sağlık iddiası yok. Doğadan toplanan mantar yenmesini teşvik eden ifade yok; sadece "doğadan toplananlar iyice yıkanır" (ATK).

## HOOK A/B
- A (VO + ekran): "Mantarı yıkarsan sünger olur mu? Tarttık." — ekran: "Mantar yıkanınca sünger olur mu?" (5 kelime)
- B (VO + ekran): "Bu iki mantardan biri suyu emiyor." — ekran: "Biri suyu emiyor, biri itiyor" (5 kelime)
Test: tek değişken hook (A = efsane sorusu, B = görsel çelişki); konu ve görseller aynı. W44 #1: soru/iddia ilk 3 sn'de. Ölçüt: stayed-to-watch (Studio'da doğrula).

## SES
- 0,0 sn: iki mantarın aynı anda su kâsesine düşüşü "blup-blup" (özgün Foley) + mutfak tartısının "bip" sesi — VO aynı karede başlar, selam/giriş yok.
- Doğal Türkçe anlatım, ~2,6 kelime/sn; telifsiz düşük ritim altlık.
- 8 sn: su damlalarının beyaz mantar şapkasından kayıp düşmesi "tıp tıp" (burkulma 1: itiyor).
- 15 sn: istiridye mantarı sıkılınca su "şırr" (burkulma 2: açık lamel).
- 21 sn: bıçakla doğrama "tak tak" + kesik dilimin suya batışı (burkulma 3: kesip yıkama).
- 24 sn: tavada cızırtı.
- Son 1 sn: tartı "bip" → başa (loop köprüsü).
VO metni (Hook A sürümü):
0–3: "Mantarı yıkarsan sünger olur mu? Tarttık."
3–8: "Bir testte 252 gram mantar beş dakika suda kaldı; kurulanınca sadece 6 gram ağırlaştı."
8–13: "Çünkü mantar, yüzeyinde suyu iten proteinler salgılıyor; damla şapkadan kayıp gidiyor."
13–19: "Ama burkulma şu: alt yüzü açık, ince yapraklı mantarlar, istiridye ve shiitake gibi, bir dakikada ağırlığının dörtte birine kadar su çekebiliyor."
19–23: "Ve mantarı doğradıktan sonra yıkarsan, kesik yüzey suyu sünger gibi alıyor."
23–26: "Kısacası: kültür mantarını bütünken hızlıca durula, kurula, hemen pişir; yapraklıları fırçayla sil."
26–28: "Şimdi tartıya koy..." → başa: "Mantarı yıkarsan sünger olur mu? Tarttık."

## SAHNELER
1. 0–3 sn: Mutfak tartısı ekranında gram değeri; iki mantar (beyaz kültür mantarı + istiridye) aynı anda su kâsesine düşer (yavaş çekim, sıçrama). Ekran yazısı (hook).
2. 3–8 sn: Tartı yakın plan: "önce / sonra" iki kare, Cerno grafiğiyle büyük rakamlar 252 g → 258 g, altında küçük "McGee testi" etiketi. Ekran: "5 dakika suda: +6 gram".
3. 8–13 sn (burkulma 1): Beyaz mantar şapkası makro; su damlası boncuk gibi durup kayar. Özgün 2D katman (HyperFrames): yüzeyde minik "kalkan" pulları damlayı iter (sayı yok). Ekran: "Yüzeyi suyu itiyor".
4. 13–19 sn (ÖDÜL, 13–15. sn): Mantar ters çevrilir; istiridye/shiitake lamelleri makro. Bölünmüş ekran: solda beyaz mantar tartıda neredeyse aynı, sağda istiridye mantarı sıkılınca su akar. Grafik çubuk: "lamelsiz ≈ 0" vs "açık lamelli %25'e kadar (1 dk)". Ekran: "Yapraklı olan sünger gibi".
5. 19–23 sn (burkulma 3): Doğranmış dilimler suya batırılır; kesik yüzeyden hava kabarcıkları çıkar (su içeri girerken). Ekran: "Doğrayıp yıkama".
6. 23–26 sn (çözüm): Bütün beyaz mantar akan suda 3–5 sn durulanır → salata kurutucuda döner → sıcak tavada kızarır. Yanında istiridye mantarı kâğıt havluyla silinir. Ekran: "Bütünken durula, hemen pişir".
7. 26–28 sn: El mantarı tartıya koyar, "bip" → match cut sahne 1'deki tartı ve düşüş anına (loop).
Kural: her 2–4 sn yeni görsel; ödül 13–15. sn'de (25'ten önce).

## İLK KARE
Hareket halinde: iki mantar havada, su kâsesine düşmek üzere; ön planda dijital mutfak tartısı rakamı yanıp sönüyor; üstte büyük, okunur yazı "Mantar yıkanınca sünger olur mu?". Siyah/boş kare yok, logo yok, yüz yok, tartı/ambalajda marka görünmüyor.

## KAPAK
"MANTAR YIKANIR MI?" (3 kelime) — tartı üstünde ıslak beyaz mantar, yanında su damlayan istiridye mantarı.

## BAŞLIK
Önerilen: Mantar Yıkanır mı? 5 Dakika Suda Sadece 6 Gram
Alternatif: Why You Can Wash Mushrooms (Except These) / Mantar Neden Su Çekmez? 1 İstisna Var

## AÇIKLAMA
"Mantar yıkanmaz, sünger gibi su çeker" diye bilinir. Harold McGee'nin testinde 252 g mantar 5 dakika suda kaldıktan sonra yalnızca 6 g ağırlaştı. America's Test Kitchen'ın tartı testinde lameli (alttaki ince yaprakları) açıkta olmayan mantarlar neredeyse hiç su tutmadı; istiridye, shiitake gibi açık lamelliler ise 1 dakikada ağırlıklarının %25'ine kadar su çekti. Doğranmış mantar da kesik yüzeyden su alır. Kültür mantarını bütünken hızlıca durulayıp kurulayın ve hemen pişirin; açık lamellileri fırçayla ya da kâğıt havluyla silin.
Kaynaklar: America's Test Kitchen; Serious Eats; The Guardian (Harold McGee testi).
#shorts #mutfak #yemekbilimi

## TAG
#shorts #mutfak #mutfakbilgisi #yemekbilimi #mantar #mutfakipuçları #yemekefsaneleri #bilim
Etiket alanı: mantar yıkanır mı, mantar nasıl temizlenir, mantar su çeker mi, kültür mantarı yıkama, istiridye mantarı temizleme, shiitake yıkanır mı, mantar neden suluyor, mantar kızartma ipucu, should you wash mushrooms, do mushrooms absorb water

## PIN
"Siz mantarı yıkıyor musunuz, siliyor musunuz?"
(Konuyla ilgili soru; abone/ürün çağrısı yok.)

## PROMPT
Görsel üretim / çekim (9:16, gerçekçi, logo/marka yok, insan yüzü yok). Gerçek çekim tercih: dijital mutfak tartısı (markası bantlı), beyaz kültür mantarı, istiridye ve/veya shiitake mantarı, cam kâse, salata kurutucu, bıçak, tava, kâğıt havlu; telefonla 120–240 fps + ayrı yakın mikrofon Foley.
- S1: "Vertical 9:16, slow motion of a white button mushroom and an oyster mushroom dropping into a clear glass bowl of water, splash, digital kitchen scale in foreground, motion from the first frame, soft kitchen light, no labels, no brand logos"
- S2 rakam grafiği, S3 kalkan katmanı, S4 çubuk grafik: özgün 2D (HyperFrames compose); rakamlar yalnızca kaynaktakiler (252 g → 258 g; "%25'e kadar, 1 dk, açık lamelli"), uydurma sayı yok.
- S3, S4, S5, S6: gerçek çekim: şapka üstünde boncuklanan damla makro; istiridye mantarının sıkılınca su bırakması; doğranmış dilimlerin suya batışı; durula → salata kurutucu → tava.
- Gerçek tartı testi önerisi: çekimde kendi tartımızla beyaz mantar ve istiridye mantarını 1 dk batırıp öncesi/sonrası tart; sonuç ekranda gösterilecekse kendi değerimiz "bizim testimiz" diye ayrı etiketlenir, kaynak rakamlarıyla karıştırılmaz. Sonucu kaydet.
Stok tercih (çekim yoksa): Pexels/Pixabay "mushroom water splash", "washing mushrooms", "oyster mushroom gills macro"; her klip için URL + lisans kaydı. Ücretli klip yok. Marka görünmez.

## LOOP
Son replik "Şimdi tartıya koy..." elin mantarı tartıya koymasıyla biter; tartının "bip" Foley'i köprü olur ve match cut ile frame 1'deki tartı + düşüş anına, "Mantarı yıkarsan sünger olur mu? Tarttık." repliğine bağlanır. İkinci turda izleyici cevabı bilerek tartı rakamını izler.

## ÖZGÜNLÜK NOTU
- MAYA: tanıdık = "mantar yıkanmaz" mutfak öğüdü; burkulma 1 = 5 dakika suda sadece 6 gram, yüzey suyu itiyor; burkulma 2 = efsane aslında yapraklı (açık lamelli) mantarlar ve doğranmış mantar için doğru.
- Bugün canlı rakip taraması yapılmadı; hiçbir videodan metin/görsel alınmadı. Cerno açısı: "iki mantar aynı kâsede" görsel çelişkisi + tartı rakamı + lamel istisnası + "bip" sesiyle loop.
- Cerno'ya özel görseller: tartı önce/sonra rakam grafiği, damlayı iten "kalkan" katmanı, lamelsiz vs lamelli çubuk grafiği, "MANTAR YIKANIR MI?" kapağı.
- Seri bağı: "mutfak efsanesi → tartı testi" ailesi; abone çağrısı yok.

## Uygulanan öğrenmeler (knowledge/shorts/learnings)
- success-patterns §1: ilk kare hareket + ekranda soru, selam/giriş yok.
- success-patterns §2–3: ≤ 30 sn (28 sn), her 2–4 sn yeni görsel, ödül 25. sn'den önce (13–15. sn), loop.
- W44 #1: soru kalıbı ilk 3 sn'de → başlık "Mantar Yıkanır mı?".
- W44 #2: tekrarlanabilir seri (mutfak efsanesi → test ailesi).
- W44 #3: tek değişken = Hook A/B.
- W44 #4 (beğeni düşük): görsel çelişki (aynı kâsede iki mantar) + PIN'de taraf seçtiren soru.
- W44 #5–6 (stayed düşük, kısa izleme): düşüş + sıçrama + tartı sesiyle açılış, rakam 3. sn'den itibaren, loop.
- W44 #7 (seri sözü): abone çağrısı yasak olduğundan seri bağı sadece içerik ailesiyle kuruluyor.

## Yayın öncesi kontrol
- [x] Bilimsel iddialar kaynaklı (America's Test Kitchen x2, Serious Eats, The Guardian/McGee) ve test koşullarıyla sınırlı ifade edildi
- [x] Yer tutucu metin yok; animasyonda uydurma sayı yok
- [x] Abone/ürün baskısı yok, marka görünmüyor
- [x] Sağlık/hijyen iddiası yok; yabani mantar toplama teşvik edilmiyor
- [ ] İsteğe bağlı kendi tartı testimiz çekimde yapılırsa sonucu kaydedilecek
- [ ] Gerçek hareketli görüntü + lisans kaydı
- [ ] MP4 render + tam süre QC
- [ ] Furkan "yayınla" onayı (onay ve video URL'si olmadan yükleme yok)
