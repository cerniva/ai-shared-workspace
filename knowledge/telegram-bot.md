# Telegram Botu (ücretsiz, GitHub Actions üzerinde)

Bot `scripts/telegram_bot.py` ile çalışır; `.github/workflows/telegram-bot.yml` her 5 dakikada bir mesajları çeker (cevaplar en fazla ~5 dk gecikir). Grok Bot'tan bağımsızdır, harici sunucu yoktur.

## Furkan için kurulum
1. Telegram'da **@BotFather**'a `/newbot` yaz, isim ve kullanıcı adı ver.
2. BotFather'ın verdiği **token**'ı kopyala.
3. GitHub → repo **Settings → Secrets and variables → Actions → New repository secret**: ad `TELEGRAM_BOT_TOKEN`, değer token.
4. Telegram'da botuna `/start` gönder.
5. En geç 5 dk içinde bot **chat id**'ni yazar (Actions → telegram-bot → Run workflow ile hızlandırabilirsin).
6. Aynı yerde `TELEGRAM_ALLOWED_CHAT_ID` secret'ını (veya variable) bu chat id ile ekle. Artık bot yalnızca sana cevap verir.

## Komutlar
- `/durum` — chatgpt-to-read.md ve açık handoff özeti
- `/gorev <metin>` — ChatGPT'ye handoff (furkan→chatgpt)
- `/yedek`, `/yurutucu`, `/arastirma`, `/rapor` — ilgili ajanın (backup-supervisor, automation-runner, research-learner, agents-reporter) son çıktısını yorumlar; arkasına metin yazarsan o ajana handoff ekler; `calistir` yazarsan izinliyse workflow'u tetikler
- `/tetikle <workflow.yml>` — yalnızca check/test/render workflow'ları (yayın, ödeme, upload, deploy asla; automation-runner da tetiklenmez)
- Serbest metin — Gemini öncelikli sağlayıcı yedeklemesiyle Türkçe cevap
