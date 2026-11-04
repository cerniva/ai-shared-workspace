# improvement-bot raporu (2026-11-04, 2026W45)

Uretim: 2026-11-04T13:05:37+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 39

## Darbogazlar

**En yavas 3 workflow (medyan):**
- tinyfish-youtube-analytics: 137 sn (maks 137, 1 kosu)
- CodeQL code scanning: 63 sn (maks 111, 7 kosu)
- improvement-bot: 57 sn (maks 65, 5 kosu)
- En cok kirilan: takipci-denetci %27 (4/15)
- En uzun acik devir: HO-20261009-08 616.1 sa (open, auditor)
- En cok dusen saglayici: cerebras 160.3 sa
- En uzun bekleyen bot PR: #158 591.8 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'tinyfish-youtube-analytics' medyan 137 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 63 sn (7 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 57 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %27 (4/15). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 160.3 saat dustu (no_key 160.3, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 616.1 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 591.8 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- provider-cerebras -> HO-IMP-20261104-provider-cerebras (pending); model: gemini
