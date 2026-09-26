# Browser Worker

Playwright tabanli web-islem worker'i. GitHub Actions uzerinde Chromium acar ve verilen adimlari uygular.

Desteklenen adimlar: `goto`, `click`, `fill/type`, `press`, `wait`, `wait_for`, `extract`, `screenshot`.

## Calistirma
GitHub > Actions > Browser Worker > Run workflow. `task_json` alanina JSON gorev ver.

Ornek:
```json
{"id":"demo","steps":[{"action":"goto","url":"https://example.com"},{"action":"extract","selector":"h1"},{"action":"screenshot"}]}
```

Sonuc JSON ve ekran goruntuleri Actions artifact olarak kaydedilir.

## Guvenlik
Sifre/token gibi gizli degerleri task JSON'a veya repoya koymayin. Bunlar GitHub Actions Secrets uzerinden enjekte edilmelidir. CAPTCHA, 2FA ve dogrulama gereken adimlarda insan mudahalesi gerekir. Worker yalnizca http/https adreslerine gider.
