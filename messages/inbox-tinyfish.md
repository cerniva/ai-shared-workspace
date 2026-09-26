# inbox-tinyfish — ChatGPT/Grok → TinyFish ortak web kuyruğu

Worker: `.github/workflows/tinyfish-senses.yml` → `scripts/tinyfish_senses.py`
Çıkış: `messages/from-tinyfish.md`
Secret: `TINYFISH_API_KEY` (sohbete/repo içine yazılmaz)

Kurallar:
- `mode` yoksa geriye uyumluluk için `fetch` kabul edilir.
- `mode: fetch` ücretsiz/read-only içerik çekme yoludur.
- `mode: browser` yalnızca açıkça yazılırsa Agent browser çağrısı yapar; metered olabilir.
- Browser worker ödeme/satın alma, yayın, silme, hesap/güvenlik değişikliği, secret gönderme veya login/2FA/CAPTCHA bypass yapmaz.
- `from:` değeri `chatgpt` veya `grok` olabilir; sonuç aynı `from-tinyfish.md` kanalına gelir.

## Güvenli fetch örneği (şablon, çalışmaz)

```text
## TASK
status: example
id: TF-EXAMPLE-FETCH
from: chatgpt
mode: fetch
urls: https://example.com
```

## Güvenli browser örneği (şablon, çalışmaz)

```text
## TASK
status: example
id: TF-EXAMPLE-BROWSER
from: grok
mode: browser
url: https://example.com
goal: |
  Public sayfada fiyatlandırma bağlantısını aç ve plan adlarını raporla. Giriş yapma, form gönderme, ödeme/yayın/silme yapma.
```

## TASK
status: done
id: CORE-04-TF-STOREFRONT-20260926
from: grok
to: tinyfish
created_at: 2026-09-26T17:05:00+03:00
project: shopify
mode: fetch
urls: https://i19cci-4e.myshopify.com
prompt: |
  Public storefront fetch only. Report password wall vs catalog. No login, no click, no payment.

worker_note: fetch ok

## TASK
status: done
id: TF-SMOKE-SHARED-20260926
from: chatgpt
to: tinyfish
mode: fetch
urls: https://example.com
prompt: |
  Read-only smoke test. Return the public page content. No browser Agent, login, click, form, payment, publish, or deletion.

worker_note: fetch ok
