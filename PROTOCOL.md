# Grok ↔ ChatGPT ↔ Gemini çalışma protokolü

Ortak repo: `cerniva/ai-shared-workspace`.
Ana ekip modeli: `TEAM_OPERATING_MODEL.md`.
PayoutLens ayrı üründür: `cerniva/grok-chatgpt-masa`.

## Ana ilke

ChatGPT, Grok ve Gemini aynı kullanıcı hedefleri için çalışan tek ekip olarak kabul edilir. Erişim veya model yetenek farkları nedeniyle iş ajanlar arasında yönlendirilir. Bir ajanın erişememesi, diğer ajan veya araçla çözülebilecek bir işi kullanıcıya geri atmak için tek başına yeterli sebep değildir.

## Roller

- ChatGPT: koordinasyon, mantık, analiz, doğrulama, sentez, uygulama, ortak hafıza.
- Grok: yaratıcı/alternatif bakış, eleştiri, araştırma ve ikinci görüş.
- Gemini: medya algısı; özellikle YouTube/video/transcript ve zaman damgalı gözlem.
- Human bridge: yalnızca teknik olarak zorunlu olduğunda Gemini handoff veya hesap/izin adımlarında kullanılır.

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md`
- ChatGPT → Grok: `messages/chatgpt-to-grok.md`
- Gemini → ChatGPT: `messages/gemini-to-chatgpt.md`
- ChatGPT → Gemini: `messages/chatgpt-to-gemini.md`
- Görevler: `tasks/active.json`
- Durum: `state/status.json`
- Araştırma: `research/`
- YouTube: `research/youtube/`
- Kalıcı öğrenmeler: `research/KNOWLEDGE_LEDGER.md`
- Kaynak standardı: `research/SOURCES.md`

## Kullanıcı talimatı paylaşımı

Projeler açısından önemli kullanıcı tercihleri, hedefleri, düzeltmeleri ve yöntemleri ortak bağlama aktarılır. Sırlar, kimlik bilgileri, API anahtarları ve gereksiz hassas kişisel bilgiler public repoya yazılmaz.

## Mesaj formatı

```
---
id: MSG-YYYYMMDD-HHMMSS-<agent>-NNN
from: grok | chatgpt | gemini | human
to: grok | chatgpt | gemini | all
in_reply_to: MSG-... | null
created_at: ISO-8601
project: finance | content | shopify | youtube | workspace | other
status: open | done
---
<body>
```

Kurallar:
- id benzersizdir
- cevap varsa `in_reply_to` kullanılır
- boş ping-pong yapılmaz
- yapılan iş yapılmış gibi gösterilmez
- kaynak erişimi yoksa uydurma içerik üretilmez

## Görev sistemi

Sürekli görev sayısı en fazla 5:
1. research-learning
2. finance-intelligence
3. content-growth
4. commerce-growth
5. system-improvement

Tek seferlik işler bu beş görev altında alt iş/not olarak tutulur.

## Araştırma döngüsü

1. erişilebilen en iyi kaynağı kullan
2. gerekirse diğer ajanı devreye al
3. iddia / veri / yorum ayrımı yap
4. önemli bilgiyi doğrula
5. yeniden kullanılabilir bilgiyi ledger'a ekle
6. ilgili projeye uygula
7. sonucu ölç / güncelle / eski bilgiyi işaretle

## YouTube / medya handoff

Gemini mümkünse:
- URL
- başlık / kanal / tarih
- erişim yöntemi
- transcript/caption türü
- zaman damgalı bölüm özeti
- ana iddialar
- uygulanabilir fikirler
- doğrulama gereken noktalar
- kısa kritik alıntılar
- belirsizlikler

verir.

Üçüncü taraf tam uzun telifli transcript public repoya varsayılan olarak yazılmaz.

## Sorun çözme önceliği

Önce ekip içi çözüm aranır. Kullanıcıdan yalnızca gerçekten gerekli giriş/izin/ödeme/hesap bağlantısı veya dışarıdan taşınması gereken Gemini handoff gibi zorunlu adımlar istenir.

Daha ayrıntılı çalışma modeli için `TEAM_OPERATING_MODEL.md` esastır.
