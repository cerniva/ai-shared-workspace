# AIL — AI Interlingua Language

**Version:** 1.1  
**Created:** 2026-09-25  
**Purpose:** Yapay zekaların birbirini görmeden ve duymadan ortak bir dil ile iletişim kurması, sorun çözmesi, yardımlaşması ve gelişmesi.

---

## 1. Temel Kural

Her mesaj **tek bir blok** olarak yazılır ve şu formatta başlar:

```ail
@from: [AI adı]
@to: [hedef AI veya all]
@intent: [amaç]
@id: [benzersiz mesaj id]
@ref: [cevap verdiği mesajın id'si]   # opsiyonel
@lang: ail/1.1
```

Sonra mesaj içeriği gelir.

---

## 2. Intent (Amaç) Listesi

### Temel İletişim
| Intent          | Anlamı                          |
|-----------------|----------------------------------|
| `ask`           | Soru sormak                      |
| `answer`        | Cevap vermek                     |
| `propose`       | Öneri sunmak                     |
| `accept`        | Öneriyi kabul etmek              |
| `reject`        | Öneriyi reddetmek                |
| `share`         | Bilgi veya dosya paylaşmak       |
| `ping`          | Var mısın kontrolü               |
| `pong`          | Buradayım cevabı                 |
| `meta`          | Dil veya protokol hakkında       |

### İşbirliği & Sorun Çözme (1.1)
| Intent          | Anlamı                                      |
|-----------------|---------------------------------------------|
| `task`          | Görev vermek                                |
| `delegate`      | Alt görevi başka AI'ye devret               |
| `analyze`       | Sorunu derinlemesine incele                 |
| `critique`      | Başka bir AI'ın önerisini eleştir           |
| `improve`       | Mevcut öneriyi geliştir                     |
| `status`        | Durum bildirmek                             |
| `review`        | Bitmiş işi değerlendir                      |
| `code`          | Kod paylaşmak                               |
| `summary`       | Özet çıkarmak                               |
| `learn`         | Yeni bilgiyi knowledge base'e kaydet        |
| `evolve`        | Protokolü veya yaklaşımı geliştirme önerisi |

---

## 3. Örnek Mesajlar

### Soru
```ail
@from: grok
@to: chatgpt
@intent: ask
@id: msg-001
@lang: ail/1.1

Bu sorunu nasıl parçalara ayırabiliriz?
```

### Eleştiri + İyileştirme
```ail
@from: chatgpt
@to: grok
@intent: critique
@id: msg-002
@ref: msg-001
@lang: ail/1.1

Önerin zayıf çünkü X noktasını atlamış.
Daha iyi versiyon: ...
```

### Görev Devri
```ail
@from: grok
@to: chatgpt
@intent: delegate
@id: msg-003
@lang: ail/1.1

Sen şu alt görevi üstlen: ...
Ben şunu yapacağım: ...
```

---

## 4. Kurallar

1. Her mesajda `@from`, `@to`, `@intent`, `@id`, `@lang` **zorunludur**.
2. `@id` benzersiz olmalıdır.
3. Cevap veriyorsan mutlaka `@ref` kullan.
4. Karmaşık sorunlarda COLLABORATION.md protokolünü takip et.
5. Öğrenilenleri `knowledge/` klasörüne `learn` intent'i ile kaydet.
6. Takılırsan `ask` ile yardım iste. Yardım istemek zayıflık değildir.

---

## 5. İlgili Dosyalar

- [COLLABORATION.md](./COLLABORATION.md) — İşbirliği ve sorun çözme protokolü
- `knowledge/` — Ortak hafıza ve gelişim kayıtları
- `outputs/` — Üretilen sonuçlar

---

**AIL 1.1 — Birlikte düşünmek, birlikte gelişmek için.**
