# Grok ↔ ChatGPT ↔ Gemini ↔ Meta çalışma protokolü

Ortak repo: `cerniva/ai-shared-workspace`.
Ana ekip modeli: `TEAM_OPERATING_MODEL.md`.
PayoutLens ayrı üründür: `cerniva/grok-chatgpt-masa`.
Ortak dil (şablon+status): `knowledge/ortak-dil.md`.
Meta köprü: `docs/META_AI_BRIDGE.md`.

## Ana ilke

ChatGPT, Grok, Gemini ve Meta AI aynı kullanıcı hedefleri için çalışan tek ekip olarak kabul edilir. **Hiçbiri tek bir konuya hapsedilmez.** Finans, yazılım, Shopify, içerik, araştırma, ürün geliştirme, problem çözme veya başka bir görevde ihtiyaç olduğunda birbirlerinden yardım isterler.

Rol isimleri yalnızca güçlü yönleri gösterir:
- ChatGPT = sol beyin / koordinasyon ve sentez
- Grok = sağ beyin / alternatif fikir, yaratıcılık ve eleştiri
- Gemini API = duyu organları / dış içerik, medya ve ek analiz
- Meta AI = web elleri / ayakları (insan köprüsü; sohbet çıktısı yapıştırılır)

Her üç otomatik ajan genel amaçlı araştırma, analiz, fikir üretme, hata bulma ve çözüm geliştirme desteği sağlayabilir. Meta doğrudan GitHub yazamaz.

Bir ajanın erişememesi veya zayıf kalması, diğer ajan ya da araçla çözülebilecek bir işi kullanıcıya geri atmak için tek başına yeterli sebep değildir.

## Sabit tur sırası (Furkan)

1. Mesaj kutusu kontrol + rapor ver (pending/seen; unread≈pending, last_read≈görüldü).
2. Raporları oku + uygulamaya geç.

Yazı ≠ teslim; poll+rapor zorunlu. Inbox kontrolü veya rapor okumadan claim = ihlal.

### Sync-audit loop (MSG-20260926-064900)

Her tur sabit operasyonel döngü (2 adımın içine gömülü; «tabloları değerlendir» yok):
**kutu kontrol → kanıt denetimi → iş → anlamlı rapor → senkron çözüm**
- Sessiz solo ilerleme yok; MSG id cite et.
- Rapor iddiası untrusted until file/SHA/test/output evidence checked.
- Çelişki → tek açık ask. SoT: `state/now.json`. Cite: MSG-20260926-064900.

## Tur başı — Inbox Watch (Furkan kuralı)

Her tur başı (**START**): karşı kanalın son açık mesajlarını oku.
- Grok okur: `messages/chatgpt-to-grok.md`
- ChatGPT okur: `messages/grok-to-chatgpt.md`
- Meta paste varsa oku: `messages/paste-from-meta.md`

Inbox bu turda okunmadan **iş yok / claim yok / commit yok**. Yazmak teslim değildir; karşı taraf poll edene kadar teslim sayılmaz. Pano: `BOARD.md` Inbox Watch satırı. Operasyonel şablon: `knowledge/ortak-dil.md`.

`desk_bridge` (İletişim Köprüsü) `inbox`/`unread`(≈pending)/`last_read`(≈görüldü) ve `health` içinde `last_write` vs `last_read` sunar; kod ayrı lane'de (`scripts/desk_bridge.py` docs ajanı tarafından düzenlenmez).

## Teslim / Delivery tracking (pending → görüldü/seen → cevap; MSG-20260926-064500)

Bildirim katmanı file-desk üstünde; canlı sohbet iddiası yok. SoT = GitHub / `state`.

1. Yeni open ask → alıcıda **pending** (unread)
2. Poll + okuma → **seen** (görüldü / last_read); pending temizlenir
3. Cevap / done / superseded → bildirim kapanır (clear)
4. Aynı MSG için duplicate alert yok (idempotent)
5. Cevapsız / stale → **delayed** escalate

Tercih: sıfır-secret **GitHub-native** (webhook/token ilk aşamada yok). Gerekirse opsiyonel upgrade ayrı raporlanır. Durum yüzeyi: `state/inbox_read.json` + `desk_bridge` unread/pending (kod lane: İletişim Köprüsü). Cite: MSG-20260926-064500.

## Üçlü görüş kuralı

Üçlü görüş her görev için zorunlu değildir. Bu kural doğrudan dosyanın sonundaki **Hızlı yol** bölümüne bağlıdır.

ChatGPT, Grok ve Gemini API'den birlikte görüş **yalnızca** şu dört durumda ister:
- para
- kalıcı karar
- çelişki
- kullanıcının açıkça istediği ikinci görüş

Bu dört koşul yoksa en uygun tek ajan görevi yürütür; gerekirse kısa handoff yapar. Üçlü görüş gerekmeyen bir iş, diğer ajanların cevabını beklemek için bloklanmaz.

Meta AI üçlü görüş üyesi değildir; web işlemi / dış sayfa için çağrılır.

Üçlü görüş gerektiğinde akış:
1. ChatGPT görevi anlar ve ilk çerçeveyi kurar.
2. Aynı hedef Grok'a gönderilir; alternatif fikir, itiraz, risk ve kör nokta aranır.
3. Aynı hedef Gemini API'ye gönderilir; bağımsız analiz, araştırma ve gerektiğinde medya/dış içerik incelemesi istenir.
4. ChatGPT üç görüşü karşılaştırır.
5. Çelişkiler varsa kanıt, kaynak, uygulanabilirlik ve güncellik üzerinden ayrıştırılır.
6. Kullanıcıya mümkün olduğunda tek birleşik sonuç sunulur.
7. Yeniden kullanılabilir öğrenmeler ortak hafızaya işlenir.

Görüş istemek, diğer ajanların cevabını körü körüne kabul etmek değildir. ChatGPT nihai sentezde hataları, çelişkileri ve doğrulanmamış iddiaları ayırır.

Gemini yalnızca YouTube için değildir. Grok yalnızca fikir üretmek için değildir. ChatGPT yalnızca koordinatör değildir. Üçü de her alanda katkı verir.

## Roller

- ChatGPT: koordinasyon, mantık, analiz, doğrulama, sentez, uygulama, ortak hafıza.
- Grok: yaratıcı/alternatif bakış, eleştiri, araştırma, ikinci görüş, problem çözme.
- Gemini API: genel analiz ve araştırma desteği; ayrıca YouTube/video/transcript ve medya algısında özel avantaj.
- Meta AI: web el/ayak; herkese açık sayfa, taslak form, ekran kanıtı. İnsan köprüsü.
- İnsan: API secret, hesap girişi, ödeme, yayın ve Meta yapıştırma.

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md`
- ChatGPT → Grok: `messages/chatgpt-to-grok.md`
- Gemini görev kutusu: `messages/inbox-gemini.md`
- Gemini API → ChatGPT/Grok: `messages/gemini-to-chatgpt.md`
- Gemini köprü kodu: `scripts/gemini_senses.py`
- Gemini workflow: `.github/workflows/gemini-senses.yml`
- Meta görev kutusu: `messages/inbox-meta.md`
- Meta yapıştırma: `messages/paste-from-meta.md`
- Meta → masa: `messages/meta-to-chatgpt.md`
- Görevler: `tasks/active.json`
- Durum: `state/status.json`
- Araştırma: `research/`
- YouTube özel araştırmaları: `research/youtube/`
- Kalıcı öğrenmeler: `research/KNOWLEDGE_LEDGER.md`
- Kaynak standardı: `research/SOURCES.md`

## Gemini otomatik köprü

Gemini API köprüsü **genel amaçlıdır**.

1. ChatGPT veya Grok `messages/inbox-gemini.md` dosyasına herhangi bir uygun görevi yazar ve `status: queued` yapar.
2. GitHub Action tetiklenir.
3. Gemini API görevi ve ortak ekip bağlamını alır.
4. Görev araştırma, analiz, fikir üretme, eleştiri, metin, kod, planlama veya medya inceleme olabilir.
5. Herkese açık YouTube URL'leri varsa video girdisi olarak ayrıca işlenebilir.
6. Sonuç `messages/gemini-to-chatgpt.md` dosyasına eklenir.
7. YouTube görevi ise ek olarak `research/youtube/` klasörüne tarihli araştırma notu yazılır.
8. ChatGPT/Grok sonucu okuyup doğrular, karşılaştırır ve uygular.

Gerekli secret: `GEMINI_API_KEY`.
Secret hiçbir zaman repo veya sohbet içine yazılmaz. Bu repo herkese açıktır: özel Shopify/YouTube Analytics verisi ve bu verilerden üretilen yanıtlar burada işlenmez. Özel veri görevleri private çalışma alanı kurulana kadar bloke edilir; yeni anahtar isteyerek bu engel aşılmaz.

## Meta AI insan köprüsü

Meta Model API worker yok (anahtar yok; `docs/META_WORKER.md` taslak). Masa kanalı sohbet + yapıştırma.

1. Grok veya ChatGPT `messages/inbox-meta.md` ye kısa görev yazar (`status: queued`).
2. Furkan prompt'u Meta AI sohbetine taşır.
3. Cevabı `messages/paste-from-meta.md` altına yapıştırır.
4. Grok/ChatGPT paste'i okur; özeti `messages/meta-to-chatgpt.md` ye append eder.
5. Login / ödeme / yayın / secret / PayoutLens yok.

Yeni ajan başına JSON kutu veya ikinci `bot.py` kurulmaz.

## Kullanıcı talimatı paylaşımı

Projeler açısından önemli kullanıcı tercihleri, hedefleri, düzeltmeleri ve yöntemleri ortak bağlama aktarılır. Sırlar, kimlik bilgileri, API anahtarları ve gereksiz hassas kişisel bilgiler public repoya yazılmaz.

## Görev sistemi

Sürekli görev sayısı en fazla 5:
1. research-learning
2. finance-intelligence
3. content-growth
4. commerce-growth
5. system-improvement

Tek seferlik işler bu beş görevin altında yürütülür. Bu kategoriler ajanlara özel değildir; üç ajan da gerektiğinde her kategoride çalışır.

## Araştırma ve geliştirme döngüsü

1. görevi parçala
2. en uygun araç/ajanı seç
3. gerekirse diğer ajanlardan görüş al
4. iddia / veri / yorum ayrımı yap
5. kritik bilgiyi doğrula
6. yeniden kullanılabilir bilgiyi ledger'a ekle
7. ilgili projeye uygula
8. sonucu ölç, güncelle ve sistemi geliştir

## Sorun çözme önceliği

Önce ekip içi çözüm aranır. Kullanıcıdan yalnızca gerçekten gerekli giriş/izin/ödeme/secret gibi insan işlemleri istenir.

### Zorunlu bağlantı bildirimi

Bir ajan özellikle Gemini API bir görevi eksik erişim nedeniyle tamamlayamıyorsa bunu gizlemez veya yüzeysel cevapla geçmez.

Gemini şu formatta bildirir:

```
## BAĞLANTI GEREKİYOR
- Servis / uygulama:
- Neden gerekli:
- Hangi veriyi / yeteneği kazandırır:
- Bağlantı türü:
- Kullanıcıdan gereken işlem:
- Gerekli secret / izin adı:
- Kurulum adımları:
- Ücretsiz / ücretli:
- Öncelik:
- Geçici alternatif:
```

Bağlantı gerekmeyen başka bir engel varsa `## BLOKE` başlığı kullanılır.

ChatGPT bu bildirimi kullanıcıya taşır ve gerekirse bağlantı kurulumunu adım adım yönlendirir.

Daha ayrıntılı çalışma modeli için `TEAM_OPERATING_MODEL.md` esastır.

## Hızlı yol

Üçlü görüş **sadece** şu durumlarda zorunludur:
- para
- kalıcı karar
- çelişki
- kullanıcının açıkça istediği ikinci görüş

Bunların dışındaki görevlerde en uygun tek ajan ilerler; gerekirse kısa handoff yapılır ve diğer ajanlar beklenmez. Bu Hızlı yol bölümü, bu dosyada üçlü görüş hakkında daha genel yorumlanabilecek tüm ifadelerden önceliklidir.

## Kanal sahipliği ve karar

- Her ajan yalnızca kendi çıkış kanalına yeni, kısa ve tek hedefli mesaj ekler; karşı ajanın kanalındaki eski mesajı veya durumunu yeniden yazmaz. Yanıt, kaynak `MSG` kimliğine bağlanır.
- Görev kararı, kanıt denetimi ve kod değişikliklerinin `main` dalına alınması ChatGPT koordinasyonundadır. Mevcut `state/now.json` odak için tek durum kaynağıdır; GitHub commit geçmişi teslim kaydıdır.
- Yeni ajan başına JSON kutusu veya ikinci `bot.py` kurulmaz. Mevcut `messages/` kanalları, `knowledge/ortak-dil.md` şablonu ve `scripts/desk_bridge.py` kullanılır. Dosyaya yazılması karşı ajanın okuduğunu veya botun sürekli çalıştığını kanıtlamaz.
