# Task Routing & Capacity

## Kapasite
Her ajan için maksimum aktif uygulama görevi: 5.

- chatgpt: max 5
- grok: max 5
- gemini-api: max 5
- meta: max 5 (learn-store-apply; çıkış `messages/from-meta.md`)

## Çoklu görüş
Para, kalıcı karar, çelişki veya kullanıcının açıkça istediği ikinci görüşte birden fazla ajan hedeflenir. Kota/erişim engelinde mevcut ajan işi sürdürür.
Diğer görevlerde uygun tek ajan ilerler.

## Lead seçimi
1. Göreve en uygun güçlü yön
2. Gerekli erişim
3. Mevcut aktif slot
4. Son benzer görev başarısı
5. Hız / maliyet / güvenilirlik

Meta lead olabilir: public web, connector taslağı, öğrenme kaydı, sorun parçalama.
Meta lead olamaz: ödeme, OAuth, yayın, PayoutLens, secret.

## Overflow
- Lead 5 slot doluysa kapasitesi olan diğer ajan lead olur.
- Gemini API otomatik worker var.
- Grok ve Meta file-desk / insan taşıma ile yazar.
- ChatGPT sentez + merge.

## Günlük rapor
- tamamlananlar / devam / blocked / yeni öğrenmeler / uygulanan iyileştirme / slot / yarın / kullanıcı kapısı
