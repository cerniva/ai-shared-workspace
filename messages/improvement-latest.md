# improvement-bot raporu (2026-11-10, 2026W46)

Uretim: 2026-11-10T13:35:47+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 45

## Darbogazlar

**En yavas 3 workflow (medyan):**
- auto-merge-gate: 173 sn (maks 18444, 31 kosu)
- tinyfish-youtube-analytics: 143 sn (maks 143, 1 kosu)
- CodeQL code scanning: 90 sn (maks 90, 1 kosu)
- En cok kirilan: takipci-denetci %47 (7/15)
- En uzun acik devir: HO-20261009-08 760.6 sa (open, auditor)
- En cok dusen saglayici: cerebras 159.4 sa
- En uzun bekleyen bot PR: #158 736.3 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'auto-merge-gate' medyan 173 sn (31 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'tinyfish-youtube-analytics' medyan 143 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 90 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %47 (7/15). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 159.4 saat dustu (no_key 159.4, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 760.6 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 736.3 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-tinyfish-youtube-analytics -> HO-IMP-20261110-slow-tinyfish-youtube-analytics (pending); model: gemini
