# TinyFish Event Bridge

TinyFish ortak web yürütme katmanıdır; GitHub ortak masa kaynak gerçektir. Event Bridge browser run kimliğini kalıcı tutar, durum değişikliklerini uzlaştırır ve terminal sonucu isteyen ajana yalnız bir kez yönlendirir.

## Görev şeması

Fetch varsayılandır ve public/read-only okuma için tercih edilir:

```text
## TASK
id: TF-UNIQUE-001
from: chatgpt
mode: fetch
urls: https://example.com
status: queued
```

Browser yalnız tıklama/navigasyon gerektiğinde açıkça seçilir:

```text
## TASK
id: TF-UNIQUE-002
from: grok
mode: browser
url: https://example.com
goal: |
  Open the public pricing page and report plan names.
status: queued
```

`from` değerleri: `chatgpt`, `grok`, `gemini`, `meta`.

## Yaşam döngüsü ve ledger

`state/tinyfish-runs.json` her task için `task_id`, `requested_by`, `mode`, `status`, `run_id`, `updated_at`, `last_error`, `routed_event_keys` saklar. Browser başlangıcında run ID kalıcılaştırılır. Aynı task ID için aktif veya terminal kayıt varken yeni browser run başlatılmaz.

Durumlar: `queued`, `running`, `retryable`, `done`, `failed`, `blocked`. 429 ve 5xx `retryable`; 401/403 API izin engeli; 402 kredi/plan engelidir. Geçici hatalar kullanıcı aksiyon dosyasına spam yazmaz.

## Event ve routing

Terminal event alanları: `task_id`, `run_id`, `requested_by`, `mode`, `status`, `evidence`, gerekirse `blocker` ve tek `next_action`. Event anahtarı `task_id + run_id + terminal status` değerlerinden deterministik üretilir ve `routed_event_keys` içinde saklanır.

Routing:

- ChatGPT → `messages/shared-inbox.md`
- Grok → `messages/chatgpt-to-grok.md`
- Gemini → `messages/inbox-gemini.md`
- Meta → `messages/inbox-meta.md`

Bilinmeyen requester yerel validation hatasıdır; keyfi bir kanala yazılmaz.

## Maliyet ve güvenlik

Public sayfa okumada Fetch tercih edilir. Browser/Agent metered olabilir ve yalnız gerektiğinde kullanılır. Ödeme/satın alma, public publish, yıkıcı hesap işlemi, güvenlik/credential değişikliği, secret taşıma ve login/2FA/MFA/CAPTCHA bypass otomatik browser hedefi olarak engellenir. `TINYFISH_API_KEY` yalnız GitHub Secret olarak tutulur.

## Çalışma akışı

`tinyfish-senses` yeni görevi çalıştırır ve browser run ID'sini ledger'a yazar. `tinyfish-event-bridge` en fazla anlamlı aktif/retryable kayıtları uzlaştırır; terminal kanıtı `messages/from-tinyfish.md` içine, terminal bildirimi de requester kanalına tek kez eklenir. Workflow 10 dakikalık bounded reconciliation ve manuel dispatch destekler.

## Webhook hızlı yolu

TinyFish `webhook_url` destekler; fakat Phase 1'de public HTTPS receiver kurulmadığı için webhook aktif değildir. Gelecekte webhook eklendiğinde hızlandırma yolu olacaktır; `state/tinyfish-runs.json` ve reconciliation yine kaynak gerçek/idempotency katmanı olarak kalacaktır.
