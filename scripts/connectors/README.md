# YouTube Data API Connector

Bu connector, ortak Gemini worker'a **yapılandırılmış YouTube verisi** sağlar.

## Sağladıkları

- video başlığı / açıklama / etiketler
- yayın tarihi
- görüntülenme / beğeni / yorum sayıları
- video süresi
- kanal istatistikleri
- üst yorumlar
- arama sonuçları

Public veri için `YOUTUBE_API_KEY` yeterlidir.
Kendi kanalımıza ait özel analytics/retention verileri için ayrıca YouTube Analytics API + OAuth gerekir.

## Secret

GitHub repository secret:

`YOUTUBE_API_KEY`

## Kaynak

Google YouTube Data API v3.
