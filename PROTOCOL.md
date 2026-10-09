# Grok ↔ ChatGPT ↔ Gemini ↔ Meta çalışma protokolü

Ortak repo: `cerniva/ai-shared-workspace`.
Ana ekip modeli: `TEAM_OPERATING_MODEL.md`.
PayoutLens ayrı üründür: `cerniva/grok-chatgpt-masa`.
Ortak dil (şablon+status): `knowledge/ortak-dil.md`.
Meta: `docs/META_AI_BRIDGE.md`. Consumer sohbet yanıtı Furkan tarafından `messages/from-meta.md` kanalına elle aktarılır.

## Ana ilke

ChatGPT, Grok, Gemini ve Meta AI **4 kişilik tek ekip**. Hiçbiri tek konuya hapsedilmez.

Rol isimleri yalnızca güçlü yönleri gösterir:
- ChatGPT = sağ beyin / yaratıcı yön, sentez ve ekip koordinasyonu
- Grok = sol beyin / mantık, kanıt kontrolü ve eleştirel çözümleme
- Gemini API = duyular / web, video, görsel-işitsel içerik ve ek algı
- Meta AI = kollar ve bacaklar / yalnızca o consumer sohbette gerçekten bağlı araçlarla sınırlı uygulama desteği

Bu benzetme katkı biçimini anlatır, görev sınırı koymaz. Gerçek araç, izin ve erişim ayrıca doğrulanır; yapılmayan işlem yapılmış gibi raporlanmaz.
Meta AI'ın consumer sohbeti GitHub connector'ı olmadığını bildirdi: GitHub dosyalarını okuyamaz/yazamaz, commit atamaz ve arka plan görevi çalıştıramaz. Yanıtların ortak repoya geçişi şu an Furkan'ın elle kopyalamasıyla olur. Meta Model API worker'ı ayrı bir otomasyondur; consumer sohbetin erişimini göstermez. Worker'da daha önce 402 billing_not_configured hatası görüldü. Secret sohbete yazılmaz.
Bir ajanın erişememesi, çözülebilir işi kullanıcıya geri atmak için yeterli değildir.

## Sabit tur sırası (Furkan)

1. Mesaj kutusu kontrol + rapor ver (pending/seen).
2. Raporları oku + uygulamaya geç.

Yazı ≠ teslim. Inbox okunmadan claim = ihlal.

### Sync-audit loop (MSG-20260926-064900)

**kutu kontrol → kanıt denetimi → iş → anlamlı rapor → senkron çözüm**
SoT: `state/now.json`.

## Tur başı — Inbox Watch

- Grok okur: `messages/chatgpt-to-grok.md` + `messages/from-meta.md` (yeni kayıt varsa)
- ChatGPT okur: `messages/grok-to-chatgpt.md` + `messages/from-meta.md`
- Meta yanıtını Furkan, doğruluğunu kontrol edip `messages/from-meta.md` kanalına elle yapıştırır. Meta consumer sohbeti inbox dosyasını kendisi okuyamaz.

`desk_bridge` kodu docs ajanı tarafından düzenlenmez.

## Teslim (MSG-20260926-064500)

pending → seen → cevap/clear. Aynı mesaj ve geçiş için ikinci uyarı yok. Okuma imleci: `state/inbox_read.json`. Teslim defteri: `state/message_delivery.json`. Sağlık: `state/desk_notify_health.json`. Koşucu: `.github/workflows/desk-notify.yml`.

Her ajan inbox okuma ve mark-read komutlarında kendi `--reader chatgpt` veya `--reader grok` kimliğini kullanır. Paylaşılan inbox ve raporlarda her ajanın imleci ayrı saklanır; birinin okuması diğerinin okunmamış kayıtlarını temizlemez.

Bu yol poll-ledger'dir; alıcı bir sonraki kontrolde görür. Sohbet push'u ayrıca test edilmeden var sayılmaz. `blocked` yanıt üst kaydı answered yapmaz. Bilgi kaydı okununca yanıt zorlanmaz. Okunmayan kayıt veya yanıtsız ask, 30 dk sonra tek `delayed` uyarısı alır.

## Her görevde ortak raporlama — zorunlu

Her anlamlı kullanıcı görevi sonunda işi yapan ajan `messages/team-reports.md` dosyasına kısa rapor ekler. Görev başında karşı ajanın son ilgili raporlarını oku; yeni rapordaki iddia ve kararları mevcut kanıtla denetle. Aynı konuya dokunan işler varsa örtüşmeyi/çelişkiyi ortak kanalda açıkça çöz; bağımsız alt işler varsa sahipleri ve sınırları böl. Nihai sentezi ChatGPT yapar.

Bu kural her görevde raporlaşmayı zorunlu kılar; her rutin görevde iki ajanın aynı işi yeniden yapmasını gerektirmez. Araştırmada işe yarar yeni kaynak, iddia ve erişim tarihiyle `research/KNOWLEDGE_LEDGER.md` içine eklenir. Tekrar kullanılabilir dersler de oraya işlenir. İlgisiz kaynak taraması yapılmaz; gizli bilgi public repoya yazılmaz.

Kanal append-only'dir. Dosya masası ortak hafızadır; canlı model-model sohbeti, anlık bildirim veya arka plan çalışması anlamına gelmez. Sohbetten dosyaya aktarım manuel kalıyorsa bu sınır raporda açıkça belirtilir.

## Görüş kuralı

Çoklu bağımsız görüş **yalnızca** para / kalıcı karar / çelişki / açık ikinci görüş için zorunludur. Diğer işte tek ajan uygulayabilir; ancak her görev raporunu ortak kanala bırakır ve karşı ajan ilgili yeni raporu okur.

## Roller

- ChatGPT: yaratıcı yön, seçenek üretme, koordinasyon ve nihai sentez; `main` merge.
- Grok: adım adım mantık, kanıt/tutarlılık denetimi, alternatif ve risk analizi.
- Gemini API: duyusal algı ve bilgi toplama; web/video/görsel-işitsel kaynaklardan yapılandırılmış bulgu.
- Meta AI: consumer sohbetinde bildirdiği arama, herkese açık Instagram içeriği, medya üretimi ve geçici Python araçlarını kullanabilir; GitHub/hesap yazımı ve kalıcı arka plan görevi yoktur. Yanıtı Furkan `messages/from-meta.md` kanalına elle aktarır.
- İnsan müdahalesi: hesap girişi/MFA, eksik OAuth kapsamına onay, ödeme veya araç tarafından açıkça istenen işlem.

## Yayın yetkisi ve doğrulama

- Furkan'ın 2026-09-26 tarihli sürekli talimatı, bağlı YouTube kanalında günlük Shorts'u rutin onay beklemeden yayımlama yetkisi verir.
- Bu yetki yalnızca doğru, bağlı kanal ve mevcut bir yayın aracı için geçerlidir; eksik OAuth kapsamını veya MFA'yı kendiliğinden sağlamaz.
- Yüklemeden önce hedef kanal ve dosya doğrulanır. Barındırılan/işlenmiş dosya, YouTube'da yayımlanmış video sayılmaz.
- API anahtarı ve `youtube.readonly` / `yt-analytics.readonly` kapsamları yalnızca okuma sağlar. YouTube API ile yükleme için `youtube.upload` kapsamı ve çalışan `videos.insert` yayın akışı gerekir.
- Yayın aracı veya gerekli kapsam yoksa tam teknik engel raporlanır; yayınlandı iddiası yapılmaz. Kullanıcıya yalnızca interaktif giriş/MFA/OAuth onayı gereken noktada dönülür.

## Eskalasyon / devir döngüsü (Furkan, 2026-10-08)

Döngü: **sorun → iki taraf bildirir → çözer → çözemezse mail ile rapor + alternatif → yapamayan devreder → birleştir → çalıştır/test et → hata varsa düzelt/tekrar → geliştir.**

1. **Kontrol:** ChatGPT ve Grok her turda birbirinin son mailini (sabit `CHATGPT-GROK` thread `1a0fa596ffcba64d`) ve GitHub deltasını (main HEAD, Actions, `messages/*`, açık issue) okur. Görev kaynağı sabit thread + repo'dur; kırpılmış `[Task Update]` bildirimi tek başına görev değildir.
2. **Bildir + çöz:** Sorunu gören taraf hemen bildirir, diğer taraf kendi kanıtıyla teyit eder. En küçük güvenli fix (kod/test/state) uygulanır; yeşil yalnız main read-back + test/CI ile.
3. **Çözülemezse:** sabit thread'e mail: aşama, engel, kanıt, denenen yol, başarısızlık nedeni, **alternatif yol**.
4. **Devir:** yapamayan taraf `handoff: kim → ne → kanıt (SHA/run/message_id)` satırı yazar; alan taraf sonraki turda üstlenir veya gerekçeyle geri verir.
5. **Birleştir → çalıştır/test → düzelt/tekrar → geliştir.** Furkan'a yalnız secret/giriş/ödeme gerektiğinde dönülür.
6. Örnek: sağlayıcı 401/403 (Issue #101) ilgisiz işi bloke etmez; `FailoverAdapter` sonraki sağlayıcıya geçer (`tests/test_provider_auth_failover.py`).

**Anti-ack kuralı:** Yalnız `GÖRDÜM` içeren mail/commit ilerleme sayılmaz. Her tur en az birini üretir: (a) görevi ilerletir (commit SHA + test/CI kanıtı), (b) devreder (handoff satırı), (c) engeli alternatifle eskale eder. GÖRDÜM gerekiyorsa bu iş/handoff/eskalasyonla aynı mailde verilir; noreply adreslerine GÖRDÜM gönderilmez.

**Stall kuralı:** Sabit thread'de >2 saat gerçek Grok iş raporu (SHA/test/handoff/eskalasyon) yoksa Grok tarafı sonraki turda iş raporu gönderir ya da açık işleri ChatGPT'ye devreder. ChatGPT bunu `STALL` olarak işaretler ve devralınabilir işi yürütür; aynı eski message_id'yi tekrar raporlamak ilerleme değildir.

## Kanallar

- Ortak görev raporları: `messages/team-reports.md`
- Grok → ChatGPT: `messages/grok-to-chatgpt.md`
- ChatGPT → Grok: `messages/chatgpt-to-grok.md`
- Gemini kuyruk / çıktı: `messages/inbox-gemini.md` / `messages/gemini-to-chatgpt.md`
- Meta Model API worker kuyruğu: `messages/inbox-meta.md` (Meta consumer sohbetine bağlı değildir; faturalандırma/secret gerektirebilir)
- Meta consumer sohbet yanıtı: Furkan elle `messages/from-meta.md` veya ham olarak `messages/paste-from-meta.md` içine aktarır
- Meta özet: `messages/meta-to-chatgpt.md`
- TinyFish ortak kuyruk / çıktı: `messages/inbox-tinyfish.md` / `messages/from-tinyfish.md`
- Görev / durum: `tasks/active.json` / `state/status.json` / `state/now.json`
