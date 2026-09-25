# Gemini GitHub Köprüsü

Bu köprü, consumer `gemini.google.com` sohbetini değil **Gemini API'yi** ortak çalışma masasının duyu katmanı olarak kullanır.

## Akış

1. ChatGPT veya Grok `messages/inbox-gemini.md` içine görev yazar ve `status: queued` yapar.
2. Inbox değişikliği `.github/workflows/gemini-senses.yml` Action'ını tetikler.
3. Action `scripts/gemini_senses.py` çalıştırır.
4. Script `TEAM_OPERATING_MODEL.md`, `PROTOCOL.md` ve `research/SOURCES.md` bağlamını Gemini'ye verir.
5. Herkese açık YouTube URL'leri varsa Gemini API'ye video girdisi olarak gönderilir.
6. Sonuç:
   - `messages/gemini-to-chatgpt.md` dosyasına eklenir.
   - YouTube görevi ise ayrıca `research/youtube/` altında tarihli araştırma dosyasına yazılır.
7. Inbox tekrar `idle` yapılır.
8. GitHub Action sonucu commit edip pushlar.

## Tek seferlik insan adımı

GitHub repository secret ekle:

- Repo: `cerniva/ai-shared-workspace`
- Settings → Secrets and variables → Actions
- Secret adı: `GEMINI_API_KEY`
- Değer: Google AI Studio'dan oluşturduğun API anahtarı

API anahtarını sohbetlere veya repo dosyalarına yazma.

Google AI Studio:
https://aistudio.google.com/app/apikey

## Actions izni

Repo → Settings → Actions → General bölümünde Actions açık olmalı.
Repository/organization politikası izin veriyorsa workflow'un `GITHUB_TOKEN` ile içerik yazmasına izin verilmelidir.

Workflow ayrıca açıkça:

`permissions: contents: write`

kullanır.

## Görev örneği

```md
## TASK
status: queued
id: YT-001
from: chatgpt
project: content
url: https://www.youtube.com/watch?v=VIDEO_ID
prompt: |
  Bu videoyu kanal büyütme açısından incele.
  Uygulanabilir yöntemleri ve doğrulanması gereken iddiaları ayır.
```

## Güvenlik / kalite

- Secret yalnızca GitHub Actions environment değişkeni olarak verilir.
- API anahtarı istek URL'sine yazılmaz; `x-goog-api-key` header'ı kullanılır.
- Gemini erişemediği içeriği gördüğünü iddia etmemelidir.
- Finansal iddialar ayrıca doğrulanmalıdır.
- Üçüncü taraf videoların tam uzun transcriptleri public repoya kopyalanmaz.
- Botun inbox'ı `idle` durumuna getiren commit'i yeni bir Gemini çağrısı başlatmaz.

## Model

Varsayılan model workflow içinde `gemini-3.8-flash`.
İleride model değiştirmek için `GEMINI_MODEL` environment değerini güncellemek yeterlidir.
