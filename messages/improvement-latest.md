# improvement-bot raporu (2026-11-26, 2026W48)

Uretim: 2026-11-26T15:27:30+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 41

## Darbogazlar

**En yavas 3 workflow (medyan):**
- tinyfish-youtube-analytics: 117 sn (maks 117, 1 kosu)
- improvement-bot: 77 sn (maks 178, 3 kosu)
- CodeQL code scanning: 76 sn (maks 90, 14 kosu)
- En cok kirilan: takipci-denetci %36 (8/22)
- En uzun acik devir: HO-20261009-08 1146.5 sa (open, auditor)
- En cok dusen saglayici: cerebras 161.7 sa
- En uzun bekleyen bot PR: #158 1122.1 sa
- YAPAMADIM notlu devir: 33
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'tinyfish-youtube-analytics' medyan 117 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 77 sn (3 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 76 sn (14 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %36 (8/22). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 161.7 saat dustu (no_key 161.7, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 1146.5 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 1122.1 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- yok (no_new_suggestion)
