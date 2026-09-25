# Grok ↔ ChatGPT ↔ Gemini çalışma protokolü

Ortak repo: `cerniva/ai-shared-workspace`.
Ana ekip modeli: `TEAM_OPERATING_MODEL.md`.
PayoutLens ayrı üründür: `cerniva/grok-chatgpt-masa`.

## Ana ilke

ChatGPT, Grok ve Gemini aynı kullanıcı hedefleri için çalışan tek ekip olarak kabul edilir. Erişim veya model yetenek farkları nedeniyle iş ajanlar arasında yönlendirilir. Bir ajanın erişememesi, diğer ajan veya araçla çözülebilecek bir işi kullanıcıya geri atmak için tek başına yeterli sebep değildir.

## Roller

- ChatGPT: koordinasyon, mantık, analiz, doğrulama, sentez, uygulama, ortak hafıza.
- Grok: yaratıcı/alternatif bakış, eleştiri, araştırma ve ikinci görüş.
- Gemini API: medya algısı; özellikle YouTube/video/transcript ve zaman damgalı gözlem.
- İnsan: yalnızca API secret, hesap girişi, ödeme veya dış servis izni gibi gerçekten zorunlu güvenlik adımlarında devreye girer.

## Kanallar

- Grok → ChatGPT: `messages/grok-to-chatgpt.md`
- ChatGPT → Grok: `messages/chatgpt-to-grok.md`
- Gemini görev kutusu: `messages/inbox-gemini.md`
- Gemini API → ChatGPT/Grok: `messages/gemini-to-chatgpt.md`
- Gemini köprü kodu: `scripts/gemini_senses.py`
- Gemini workflow: `.github/workflows/gemini-senses.yml`
- Görevler: `tasks/active.json`
- Durum: `state/status.json`
- Araştırma: `research/`
- YouTube: `research/youtube/`
- Kalıcı öğrenmeler: `research/KNOWLEDGE_LEDGER.md`
- Kaynak standardı: `research/SOURCES.md`

## Gemini otomatik köprü

Varsayılan yol artık manuel Gemini sohbeti değildir.

1. ChatGPT veya Grok `messages/inbox-gemini.md` dosyasına görevi yazar ve `status: queued` yapar.
2. GitHub Action tetiklenir.
3. Gemini API görevi ve ortak ekip bağlamını alır.
4. Herkese açık YouTube URL'leri varsa doğrudan video girdisi olarak işlenebilir.
5. Sonuç `messages/gemini-to-chatgpt.md` dosyasına eklenir.
6. YouTube görevi ise ayrıca `research/youtube/` klasörüne tarihli araştırma notu yazılır.
7. ChatGPT/Grok sonucu okuyup doğrular ve uygular.

Gerekli secret: `GEMINI_API_KEY`.
Secret hiçbir zaman repo veya sohbet içine yazılmaz.

Manuel kullanıcı köprüsü yalnızca API köprüsü çalışmıyorsa yedek yöntemdir.

## Kullanıcı talimatı paylaşımı

Projeler açısından önemli kullanıcı tercihleri, hedefleri, düzeltmeleri ve yöntemleri ortak bağlama aktarılır. Sırlar, kimlik bilgileri, API anahtarları ve gereksiz hassas kişisel bilgiler public repoya yazılmaz.

## Mesaj formatı

```
---
id: MSG-YYYYMMDD-HHMMSS-<agent>-NNN
from: grok | chatgpt | gemini-api | human
to: grok | chatgpt | all
in_reply_to: MSG-... | task-id | null
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

Önce ekip içi çözüm aranır. Kullanıcıdan yalnızca gerçekten gerekli giriş/izin/ödeme/secret gibi insan işlemleri istenir.

Daha ayrıntılı çalışma modeli için `TEAM_OPERATING_MODEL.md` esastır.
