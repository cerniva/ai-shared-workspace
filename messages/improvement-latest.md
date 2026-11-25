# improvement-bot raporu (2026-11-25, 2026W48)

Uretim: 2026-11-25T15:46:10+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 41

## Darbogazlar

**En yavas 3 workflow (medyan):**
- improvement-bot: 131 sn (maks 178, 3 kosu)
- tinyfish-youtube-analytics: 117 sn (maks 117, 1 kosu)
- CodeQL code scanning: 76 sn (maks 90, 14 kosu)
- En cok kirilan: takipci-denetci %38 (10/26)
- En uzun acik devir: HO-20261009-08 1122.8 sa (open, auditor)
- En cok dusen saglayici: cerebras 158.9 sa
- En uzun bekleyen bot PR: #158 1098.4 sa
- YAPAMADIM notlu devir: 33
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'improvement-bot' medyan 131 sn (3 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'tinyfish-youtube-analytics' medyan 117 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 76 sn (14 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %38 (10/26). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 158.9 saat dustu (no_key 158.9, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 1122.8 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 1098.4 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- yok (no_new_suggestion)
