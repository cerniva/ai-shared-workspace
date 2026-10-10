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

## Grok file-desk durumu (2026-09-26)

- `.github/workflows/grok-file-desk.yml` → `scripts/grok_senses.py` dosya kuyruğu worker'ıdır; canlı model-model sohbeti veya anlık bildirim değildir.
- Retry run başarılı çalıştı ve import sorunu giderildi. Ancak çıktı `XAI_API_KEY` GitHub Actions secret'ı eksik olduğundan `blocked` oldu; otomatik Grok model yanıtı alınmadı.
- Grok sohbetinden verilen repo inceleme yanıtı ile API worker yanıtı ayrı kaynaklardır. Birinin başarılı olması diğerinin çalıştığını kanıtlamaz.
- Grok'un sohbetinde repo okuyabildiği kendi beyanıdır; bu erişim Actions secret'ı eklemez ve API worker'ını açmaz.
- Otomatik API yanıtı gelene kadar Grok sohbeti ↔ ortak repo aktarımı elle yürütülür. Secret değeri sohbete veya repoya yazılmaz.

## Gemini kuyruk ve kota davranışı (2026-09-26)

- `messages/chatgpt-to-gemini.md` yönlendiricisi inbox'a henüz alınmamış en eski açık görevi seçer; böylece yeni bir görev eski bekleyenleri atlamaz.
- Gemini API günlük kota hatası alırsa görev kuyrukta kalır; `state/gemini-api-cooldown.json` içindeki `blocked_until` saatine kadar workflow API çağrısını atlar.
- Kotalı dönemde route adımı ve kuyruk değişiklikleri yine commit edilir; görev silinmez veya tamamlandı sayılmaz.
- Güncel testte kota kilidi aktifken Actions başarılı tamamlandı, Gemini API adımı atlandı. Günlük limit bittiği için Gemini denetim yanıtı henüz alınamadı; Gemini consumer sohbetinden elle gönderilen yanıt ayrı kanıttır.


## Aşamalı raporlama SOP (TSK-20260927-001)
`DESK.md` içindeki aşamalı raporlama adımları tüm anlamlı görevlerde uygulanır. Her kilometre taşı task ID ile ortak rapora yazılır: başlangıç; araştırma/kaynak bulundu; kaynak okundu ve kanıt denetlendi; bilgi karşı tarafa verildi; alıcı gördü; inceledi; kullandı veya gerekçeyle kullanmadı; uygulama başladı; engel/yardım istendi; çözüm başladı; test edildi; öğrenme depoya eklendi; handoff ve tamamlanma. Her kayıt zaman, aktör, durum, kanıt ve tek sonraki adımı taşır.

`seen` yalnızca gerçek okuma imleciyle kanıtlanır. `reviewed`, `used` ve `not_used` ayrı karar kayıtlarıdır; cevap yazılması bunların yerine geçmez. Yeni kaynaklar araştırma ledger'ına erişim tarihi, desteklediği bulgu ve işteki fayda/eksikliğiyle işlenir. Uygun alt işler sahipleri arasında bölünür, ortak engel birlikte çözülür. Her ajanın uygun turunda diğerinin yeni raporları okunur ve ilgili bulguya handoff ile yanıt verilir; gerçek zamanlı arka plan izleme iddiası yapılmaz. Mevcut teslim taşıması poll-ledger olduğundan sohbet push bildirimi değildir.


Task aşaması event ledger'ı `state/task_events.json` dosyasında tutulur. CLI: `python3 scripts/task_events.py log` (aynı olayın güvenli tekrarı için sabit `--event-id`) ve `python3 scripts/task_events.py list --task-id <ID>`. Bu defter rapor/audit izidir; sohbet push'u veya ajanın arka planda çalıştığının kanıtı değildir.

## Handoff sistemi (2026-10-09)

Kayıt: `state/handoffs.json`, araç: `scripts/handoff.py` (add/claim/done/merge/validate/overdue), testler CI'da.

1. Her mail aynı turda hem GÖRDÜM ile onaylanır hem de iş başlatılır; sadece onay yetmez.
2. Bir tarafın yapamadığı her iş (yazma engeli, araç yok, secret gerekir) karşı tarafa handoff maddesi olur: `id, from, to, task, reason_cannot_do, evidence`.
3. Alıcı `claim` eder, işi yapar, `done --sha <commit>` ile kapatır. SHA'sız done yok.
4. Devreden taraf SHA'yı main'den geri okuyup doğrular ve `merge` eder. Alıcı kendi işini merge edemez.
5. 2 saatten eski `open` maddeleri denetçi (auditor) `overdue` ile yükseltir; `handoff-audit` workflow'u saatlik listeler.
6. ChatGPT doğrudan yazamıyorsa: bilgi için `knowledge/promotions/*.json`, kod için `intake/chatgpt/*.patch` (bkz. intake/chatgpt/README.md).

## Uygulama botları (2026-10-10)

Furkan, ChatGPT üzerinden consumer uygulamalara repo aracılığıyla iş verir. Rehber ve başlangıç promptları: `knowledge/apps-hub.md`.

- Claude = kod inceleme → `messages/apps/claude.md`
- Gemini = araştırma → `messages/apps/gemini.md`
- Manus = web işleri → `messages/apps/manus.md`
- Lindy = mail/takvim → `messages/apps/lindy.md`
- Genspark = araştırma/rapor → `messages/apps/genspark.md`
- Perplexity = araştırma, zamanlanmış görev → `messages/apps/perplexity.md`
- Zapier Agents = otomasyon → `messages/apps/zapier-agents.md`
- n8n = GitHub/Gmail otomasyon → `messages/apps/n8n.md`
- DeepSeek = kod/mantık → `messages/apps/deepseek.md`
- Copilot (Microsoft) = Office/Outlook → `messages/apps/copilot.md`
- Mistral (Le Chat) = genel asistan / ikinci görüş → `messages/apps/mistral.md`
- Make = otomasyon → `messages/apps/make.md`
- GitHub Copilot = GitHub'da kod/PR (taslak PR; merge ChatGPT) → `messages/apps/github-copilot.md`

Kanallar append-only; kayıt: id/from/to/intent/status/evidence + en fazla 12 satır body. Açık işler `state/handoffs.json`'dan alınır. Repoya yazamayan uygulamanın yanıtını Furkan (veya ChatGPT/Grok) elle aktarır; elle aktarım raporda belirtilir.
Her uygulamanın GitHub/entegrasyon yeteneği `knowledge/apps-hub.md` içinde resmi kaynakla verilir; doğrulanmayan yetenek "doğrulanmadı" olarak işaretlidir ve test edilmeden var sayılmaz. Otomasyon araçları (Zapier, n8n, Make) yalnız kendi kanalına yazar; `.github/`, secret ve PayoutLens'e dokunmaz.
ChatGPT yöneticidir: `messages/apps/*.md` dosyalarını okur ve Furkan "uygulama botlarının durumunu özetle" dediğinde her uygulama için son kayıt, durum, kanıt ve açık işi özetler.

## Çoklu AI rolleri (2026-10-10)

Kaynak: `scripts/provider_config.py` (`PROVIDER_ROLES`, `PROVIDER_ENV`). Anahtar yoksa sağlayıcı `MissingCredential` ile atlanır; sistem çökmez.

- **Grok** (`XAI_API_KEY`): uygulayıcı / builder.
- **ChatGPT** (`OPENAI_API_KEY`): inceleme ve `main` merge kararı.
- **Gemini** (`GEMINI_API_KEY`): ikinci görüş.
- **Claude** (`ANTHROPIC_API_KEY`): kod incelemesi ve uzun metin analizi.
- **Perplexity** (`PERPLEXITY_API_KEY`): kaynaklı (citation) araştırma; kaynak URL'leri `evidence` içinde korunur.
- **DeepSeek** (`DEEPSEEK_API_KEY`): ucuz analiz ve kod.

Handoff `from/to`: `grok, chatgpt, auditor, gemini, claude, perplexity, deepseek`. Gelen kutuları: `messages/inbox-gemini.md`, `inbox-claude.md`, `inbox-perplexity.md`, `inbox-deepseek.md`. Durum: `ai-roster-check` workflow'u (elle; yalnızca secret adları raporlanır).

## GitHub-hosted ajanlar (Grok Bot'tan bağımsız, 2026-10-10)

**ChatGPT her turda önce `messages/chatgpt-to-read.md` dosyasını okur.** Bu dosyayı `agents-reporter` saatlik yazar (aynı içerik: `messages/agents-report-latest.md`).

- `backup-supervisor` (:23): handoff/CI/mesaj kontrolü, `supervisor_ok: true` küçük işler için `intake/chatgpt/` yaması; durum `messages/backup-supervisor-latest.md`.
- `automation-runner` (2 saatte bir :13): 4 otomasyonun son run'larını kaydeder (`state/automation_runner.json`); yalnız test/kontrol workflow'larını tetikler, yayın/upload workflow'larını sadece gözler.
- `research-learner` (günlük 05:37 UTC): anahtarsız birincil kaynaklardan promotion JSON'u `intake/promotions/` içine koyar; inceleyen onaylarsa `knowledge/promotions/` altına taşır.
- Model sırası: gemini → deepseek → claude → openai; anahtar yoksa model adımı atlanır. Ajan çıktısı yalnız `state/`, `messages/`, `intake/` altına yazılır; `.github/`, secret ve PayoutLens'e dokunulmaz.
