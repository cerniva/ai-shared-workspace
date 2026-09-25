# Task Routing & Capacity

## Kapasite
Her ajan için maksimum aktif uygulama görevi: 5.

- chatgpt: max 5
- grok: max 5
- gemini-api: max 5

## Zorunlu üçlü görüş
Her kullanıcı görevinde üç ajan görüşü hedeflenir.
Görüş verme ile uygulama liderliği farklıdır: herkes görüş verir, bir ajan lead olur.

## Lead seçimi
1. Göreve en uygun güçlü yön
2. Gerekli erişim
3. Mevcut aktif slot sayısı
4. Son benzer görevlerdeki başarı
5. Hız / maliyet / güvenilirlik

## Overflow
- Lead adayının 5 slotu doluysa kapasitesi olan diğer ajan lead olur.
- Gemini API bugün otomatik çalışabilir.
- Grok için tam otomatik execution ancak API bridge kurulunca mümkündür; o zamana kadar repo kuyruğu kullanılır.
- ChatGPT nihai sentez ve kullanıcıya raporlama katmanıdır.

## Günlük rapor alanları
- bugün tamamlananlar
- devam eden işler
- blocked/hata
- yeni öğrenmeler
- uygulanan iyileştirmeler
- ajan başına aktif slot
- ertesi gün öncelikleri
- kullanıcı müdahalesi gereken tek noktalar
