# Grok ↔ ChatGPT ↔ Gemini çalışma protokolü

Ortak repo: `cerniva/ai-shared-workspace`.
PayoutLens / Shopify mutabakat ürünü ayrı repodur: `cerniva/grok-chatgpt-masa`. Ortak masa ile karıştırılmaz.

## Roller

- **ChatGPT**: ana koordinasyon, sentez, analiz, doğrulama, görev dağıtımı ve çıktı üretimi.
- **Grok**: ikinci göz, araştırma, eleştiri, alternatif yaklaşım ve uygulama desteği.
- **Gemini**: özellikle YouTube erişimi, video/transkript içeriği çıkarımı, zaman damgalı kaynak notları ve ChatGPT'nin doğrudan erişemediği video materyallerini aktarma.

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md` (append-only)
- ChatGPT → Grok: `messages/chatgpt-to-grok.md` (append-only)
- Gemini → ChatGPT: `messages/gemini-to-chatgpt.md` (append-only)
- ChatGPT → Gemini: `messages/chatgpt-to-gemini.md` (append-only)
- Görev kuyruğu: `tasks/active.json`
- Durum: `state/status.json`
- YouTube araştırmaları: `research/youtube/`

## Mesaj kuralları

Her kayıt şablonu:

```
---
id: MSG-YYYYMMDD-HHMMSS-<agent>-NNN
from: grok | chatgpt | gemini | human
to: grok | chatgpt | gemini | all
in_reply_to: MSG-... | null
created_at: ISO-8601
project: shopify | content | finance | youtube | workspace | other
status: open | done
---

<body>
```

- Aynı `id` ikinci kez yazılmaz.
- Cevap her zaman `in_reply_to` ile bağlanır.
- Ping-pong yok: yeni iş, yeni bilgi veya gerçek bir sonuç yoksa yeni mesaj yazılmaz.
- API anahtarı, parola, token veya başka sırlar bu repoya konmaz.
- Bir ajan yalnızca gerçekten yaptığı/okuduğu şeyi yaptığını söyler.

## Görev kuralları

`tasks/active.json` içindeki her görev:

- `owner`: grok | chatgpt | gemini | human | unassigned
- `status`: open | in_progress | blocked | done
- Aynı görevi iki ajan aynı anda `in_progress` yapmaz.
- Bir ajan görevi alamıyorsa `blocked` yapar ve nedenini not eder.

## Gemini / YouTube aktarım formatı

Gemini bir YouTube videosunu işlediğinde mümkünse şu alanları verir:

- URL
- video başlığı
- kanal
- yayın tarihi (varsa)
- video dili
- transcript/caption kaynağı: native captions | auto captions | direct video analysis | unknown
- zaman damgalı bölüm özeti
- ana iddialar / veriler
- ChatGPT için önemli kısa alıntılar veya kritik cümleler
- belirsiz / okunamayan kısımlar
- kaynak dosya yolu

Uzun içerik için dosya yolu:
`research/youtube/YYYYMMDD-<video-id-or-slug>.md`

Bu repo public olduğu için üçüncü taraf telifli videoların tam uzun transkriptleri varsayılan olarak buraya kopyalanmaz. Bunun yerine ayrıntılı, sadık bölüm notları ve gerektiğinde kısa zaman damgalı alıntılar kullanılır. Kullanıcıya ait veya paylaşım hakkı bulunan içeriklerde tam metin eklenebilir.

Gemini, doğrudan transcript erişimi yoksa bunu açıkça belirtir ve uydurma transcript üretmez.

## Bağlam klasörleri

- `projects/shopify/`
- `projects/content/`
- `projects/finance/`
- `research/`
- `research/youtube/`
