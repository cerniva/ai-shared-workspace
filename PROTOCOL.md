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
- Araştırma kaynakları ve öğrenme ilkeleri: `research/SOURCES.md`
- Yeniden kullanılabilir öğrenmeler: `research/KNOWLEDGE_LEDGER.md`

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

## Sürekli öğrenme ve uygulama döngüsü

YouTube videoları ve transcript/caption verisi yalnızca özet çıkarmak için değil, ortak çalışma sistemini geliştirmek için de kullanılabilir.

Öncelikli öğrenme alanları:
- yatırım/piyasa haberleri ve finansal eğitim
- YouTube Shorts ve kanal büyütme
- Shopify/e-ticaret mağazası geliştirme
- içerik üretimi, SEO, reklam, dönüşüm ve ürün araştırması
- kullanıcının aktif projeleriyle ilgili yeni yöntem ve araçlar

Her yararlı kaynak için şu döngü uygulanır:
1. Kaynağı oku/izle ve erişim yöntemini kaydet.
2. Ana iddiaları ve uygulanabilir fikirleri çıkar.
3. Tarihe duyarlı bilgileri güncellik açısından kontrol et; kritik finansal iddiaları mümkünse bağımsız kaynaklarla doğrula.
4. Kanıt düzeyini ayır: kaynakta söylenen / doğrulanan / yorum veya deneyim.
5. Tekrar kullanılabilecek öğrenmeyi `research/KNOWLEDGE_LEDGER.md` içine ekle.
6. Aktif projeye uygulanabiliyorsa ilgili proje klasörüne somut aksiyon, test veya değişiklik önerisi ekle.
7. Sonuç kötüleşirse veya yeni bilgi eski bilgiyi geçersiz kılarsa eski notu silmek yerine güncelleme tarihi ve gerekçesiyle işaretle.

YouTube tek başına güvenilirlik garantisi değildir. Özellikle yatırım konularında içerik üreticisinin iddiaları kaynak olarak etiketlenir; doğrulanmamış tahminler gerçek veya kesin sonuç gibi kullanılmaz.

Bu ortak repo, sohbetler arasında tekrar kullanılabilen çalışma hafızasıdır; ancak ajanların arka planda kesintisiz kendi kendine çalıştığı varsayılmaz. Yeni araştırma görevleri kullanıcı talebi, görev kuyruğu veya zamanlanmış çalışma ile tetiklenir.

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
- uygulanabilir fikirler / deneyler
- ChatGPT için önemli kısa alıntılar veya kritik cümleler
- doğrulama gerektiren iddialar
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
