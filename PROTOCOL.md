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

pending → seen → cevap/clear. Duplicate alert yok. SoT: `state/inbox_read.json`.

## Görüş kuralı

Çoklu görüş **yalnızca** para / kalıcı karar / çelişki / açık ikinci görüş.
Diğer iş: en uygun tek ajan. Meta bu dört durumda 4. görüş olabilir; zorunlu değil.

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

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md`
- ChatGPT → Grok: `messages/chatgpt-to-grok.md`
- Gemini kuyruk / çıktı: `messages/inbox-gemini.md` / `messages/gemini-to-chatgpt.md`
- Meta Model API worker kuyruğu: `messages/inbox-meta.md` (Meta consumer sohbetine bağlı değildir; faturalandırma/secret gerektirebilir)
- Meta consumer sohbet yanıtı: Furkan elle `messages/from-meta.md` veya ham olarak `messages/paste-from-meta.md` içine aktarır
- Meta özet: `messages/meta-to-chatgpt.md`
- TinyFish ortak kuyruk / çıktı: `messages/inbox-tinyfish.md` / `messages/from-tinyfish.md`
- Görev / durum: `tasks/active.json` / `state/status.json` / `state/now.json`

## TinyFish ortak web yürütme katmanı

TinyFish, dört ajan için ortak web eli/ayağıdır; karar verici değildir. `state/now.json` sistem SoT'u, ChatGPT karar/merge koordinatörü olarak kalır.

- `from: chatgpt|grok|gemini|meta` ile dört ajan da `messages/inbox-tinyfish.md` kuyruğuna görev bırakabilir.
- Varsayılan `mode: fetch`: read-only sayfa içeriği; eski `urls:` görevleri geriye uyumludur.
- `mode: browser`: yalnızca açıkça seçildiğinde TinyFish Agent browser çalışır ve metered olabilir.
- Browser modu public gezinme/tıklama ve hassas olmayan form hazırlama içindir; ödeme/satın alma, dış yayın, silme, hesap/güvenlik değişikliği, secret gönderme veya login/2FA/CAPTCHA bypass yapmaz.
- Sonuçlar `messages/from-tinyfish.md` kanalında task id/requester/mode/status ile normalize edilir.
- Secret: `TINYFISH_API_KEY`; repo/mesaj içine yazılmaz.
- Aynı açık bağlantı/izin engeli tekrar tekrar kullanıcıya bildirilmez.

### TinyFish Event Bridge

- Kalıcı run ledger: `state/tinyfish-runs.json`.
- Browser görevi başlatıldığında `run_id` kalıcılaştırılır; aynı task ID `running`, `retryable` veya terminal durumdayken ikinci browser run açılmaz.
- Yaşam döngüsü: `queued → running → done|failed|blocked`; geçici 429/5xx için `retryable` kullanılır.
- Terminal event `task_id + run_id + status` anahtarıyla yalnız bir kez yönlendirilir.
- ChatGPT sonucu `messages/shared-inbox.md`, Grok `messages/chatgpt-to-grok.md`, Gemini `messages/inbox-gemini.md`, Meta `messages/inbox-meta.md` üzerinden alır.
- 401/403 API izin ve 402 kredi/plan engelleri deduplikasyonlu kullanıcı aksiyonu üretir. 429/5xx kullanıcı bildirimi spam'i üretmez.
- GitHub ortak masa kaynak gerçektir; event bridge yalnız anlamlı durum değişikliklerini taşır.
- Webhook hızlı yolu ileride eklenebilir; şu anda aktif değildir.

## Gemini otomatik köprü

`inbox-gemini.md` queued → Action → `gemini-to-chatgpt.md`.
Secret: `GEMINI_API_KEY` (repo içine yazılmaz).

## Meta iletişim yolları

- **Consumer Meta AI sohbeti:** Bu oturum araçlarıyla arama, herkese açık Instagram içeriklerini görüntüleme, medya üretimi ve geçici Python dosyaları yapabildiğini bildirdi. GitHub connector'ı, hesap yönetimi veya kalıcı arka plan görevi yok. Furkan, görev metnini sohbete taşır ve yanıtı `messages/from-meta.md` ya da önce `messages/paste-from-meta.md` dosyasına elle aktarır.
- **Meta Model API worker:** `inbox-meta.md` kuyruğunu ayrı GitHub Action işler. Bu yol consumer Meta AI sohbeti değildir; secret ve API faturalandırması gerektirir. Daha önce 402 `billing_not_configured` hatası raporlandı. Consumer sohbetin çalıştığı veya çalışmadığına dair kanıt sayılmaz.
- Hiçbir Meta yanıtı repoya otomatik yazılmış gibi sunulmaz. Secret, giriş ve ödeme bilgisi sohbete verilmez.

## Görev sistemi

Max 5 standing: research-learning, finance-intelligence, content-growth, commerce-growth, system-improvement. Dört ajan da her kategoride çalışabilir.

## Hızlı yol

Çoklu görüş sadece para / kalıcı karar / çelişki / açık ikinci görüş. Aksi halde tek ajan + kısa handoff.

## Kanal sahipliği

- Her ajan yalnızca kendi çıkış kanalına yazar; karşı kanalı rewrite etmez.
- Meta çıkışı: `messages/from-meta.md`.
- Karar / `main` merge: ChatGPT.
- SoT: `state/now.json`.
