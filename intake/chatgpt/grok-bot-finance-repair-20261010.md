# Grok Bot — Finans sorun çözme görevi

Tarih: 2026-10-10
Kapsam: Finans. PayoutLens KESİNLİKLE kapsam dışı.

## Amaç
ChatGPT'nin Finans otomasyonunda kalan teknik engelleri GitHub üzerinden çöz ve kanıtla.

## Öncelikler
1. GitHub yazma/persistence engeli: knowledge/finance_runtime_state.json ile source_catalog.json / learning_ledger.json için güvenli canonical dedup + write -> read-back yolunu doğrula. Kör overwrite yok; conflictte güncel SHA + tek bounded retry.
2. Grok ortak araştırma kanalı: Gmail gönderimi engelleniyorsa GitHub tabanlı Grok Bot intake/report yolunu fallback olarak kur/doğrula. Sahte canlı push iddiası yok.
3. Finans chart kalite kapısı: Python/matplotlib/pandas/seaborn YASAK. Gerçek doğrulanmış veriden native chart veya Wolfram fallback. Görsel gerçekten render edilmeden PASS yok.
4. Altcoin 10 gösterge paneli: ham veri -> açık metodoloji -> 0-100 bullish-support. Kalibrasyon kanıtlanamıyorsa N/A; uydurma skor yok.

## Çalışma şekli
SORUN -> KÖK NEDEN -> EN KÜÇÜK GÜVENLİ DÜZELTME -> UYGULA -> TEST -> READ-BACK -> SONUÇ.
401/403/OAuth/2FA için kör retry yapma. 429/5xx sınırlı backoff.
Mevcut repo yapısını silme/resetleme/yeniden yazma. PROTOCOL.md, knowledge/, state/, tasks/, messages/ kurallarını koru.

## İstenen kanıt
- Değişen dosyalar
- Commit SHA / PR (varsa)
- Test komutu/CI sonucu
- Persistence write-read-back sonucu
- Chart path test sonucu
- Grok fallback iletişim testi
- Her madde için PASS / FAIL / BLOCKED_EXTERNAL

Raporu repo içinde mevcut ortak iletişim düzenine uygun biçimde yaz. Sadece GÖRDÜM yazıp bırakma; aynı turda somut ilerleme/kanıt üret. ChatGPT daha sonra sonucu bağımsız doğrulayacak.
