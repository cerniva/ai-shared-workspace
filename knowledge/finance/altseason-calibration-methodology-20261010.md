# Altcoin boğa paneli kalibrasyon metodolojisi (öneri)

Durum: henüz kalibre edilmiş veri yok; tüm skorlar N/A.

## Göstergeler, dönüşüm ve yön
| # | Metrik | Girdi x | Yön | lo/hi |
|---|---|---|---|---|
| 1 | Altseason Index | 0–100 | artan | 0/100 |
| 2 | BTC dominansı | % | azalan | eğitim p10/p90 |
| 3 | ETH/BTC | 90g log getiri | artan | eğitim p10/p90 |
| 4 | TOTAL3/BTC piyasa değeri | 90g log getiri | artan | eğitim p10/p90 |
| 5 | Altcoin genişliği | 90g BTC'yi geçen uygun coin oranı | artan | 0/100 |
| 6 | Stablecoin arzı | 90g büyüme % | artan | eğitim p10/p90 |
| 7 | Altcoin spot hacmi | 30g hacim / 180g medyan | artan | eğitim p10/p90 |
| 8 | DXY | 90g değişim % | azalan | eğitim p10/p90 |
| 9 | VIX | 30g medyan | azalan | eğitim p10/p90 |
| 10 | Funding/OI aşırılığı | 30g z-score | iki uç riskli, orta bölge destekleyici | eğitimden doğrulanan parça-parça eşikler; şimdilik N/A |

## Skor
Artan: 100 * clip((x-lo)/(hi-lo),0,1).
Azalan: 100 * clip((hi-x)/(hi-lo),0,1).
lo/hi sadece geçmiş eğitim verisindeki p10/p90 ile bulunur. Aynı eşik, eksik veri, gecikme veya yanlış kaynak durumunda N/A; 50 ile doldurulmaz. Funding/OI doğrulanmış monoton olmayan fonksiyon olmadan N/A. Altseason Index'in sağlayıcı ve metodolojisi sabit tutulur. Kaynak URL, UTC as_of, ham değer, dönüşüm, lo, hi, skor ve veri kalitesi seride tutulur.

Panel 1: 1–5 (rotasyon/genişlik). Panel 2: 6–10 (likidite/risk). Tam ve uyumlu veri yoksa composite N/A; ağırlıklar ilk testte eşit, yalnız eğitimde optimize edilebilir.

## Geçmiş veri ve test
- Hedef 2020–2026 günlük UTC seri; gerçekte bulunabilen aralık raporlanmalı. Tarihsel coin evreni o gün bilinen coinlerle kurulmalı (survivorship bias önleme). Delist edilenler dahil. BTC/ETH, piyasa değeri, stablecoin arzı, spot hacmi, DXY, VIX, funding ve OI için lisanslı/doğrulanabilir kaynak listesi çıkarılmalı.
- Rolling 730 gün train, ardından 90 gün holdout test; 90 günde bir walk-forward. Train'den önce skor yok. Veri gecikmesi ve yayımlanma anı esas alınır (look-ahead engeli).
- Önceden belirlenen test etiketi: sonraki 90 günde geniş altcoin endeksi BTC'yi %10'dan fazla geçsin VE altcoin evreninin %60'ından fazlası BTC'yi geçsin. Bu araştırma tanımıdır, kesin piyasa kuralı değil.
- Baseline: yalnız Altseason Index ve sabit BTC dominans eşiği. Precision/recall, PR-AUC, false positive, rejim bazlı sonuçlar, veri eksikliği ve likidite duyarlılığı ölçülsün. Brier score yalnız çıktı gerçekten olasılığa dönüştürülüp kalibre edilirse kullanılmalı.
- Kod + verinin as_of kaydı + tekrar üretilebilir test + geçmiş train/test tarihleri saklansın. Look-ahead, survivorship, kaynak uyumsuzluğu ve tarih kayması testleri PASS olmadan validated denmesin.

Grok devri: altcoin_panel için veri adaptörleri, kalibrasyon JSON şeması, walk-forward testleri ve rapor artefaktı oluştur; veri yoksa N/A kuralını koru. Bu dosya metodolojidir, gerçekleşmiş backtest değildir.