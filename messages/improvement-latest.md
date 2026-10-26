# improvement-bot raporu (2026-10-26, 2026W44)

Uretim: 2026-10-26T11:15:47+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 24

## Darbogazlar

**En yavas 3 workflow (medyan):**
- tinyfish-youtube-analytics: 93 sn (maks 93, 1 kosu)
- CodeQL code scanning: 65 sn (maks 91, 58 kosu)
- shorts-render-tests: 60 sn (maks 2772, 23 kosu)
- En cok kirilan: shorts-render-tests %22 (5/23)
- En uzun acik devir: HO-20261009-08 398.3 sa (open, auditor)
- En cok dusen saglayici: cerebras 162.5 sa
- En uzun bekleyen bot PR: #158 373.9 sa
- YAPAMADIM notlu devir: 24
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'tinyfish-youtube-analytics' medyan 93 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 65 sn (58 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-render-tests' medyan 60 sn (23 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'shorts-render-tests' basarisizlik orani %22 (5/23). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 162.5 saat dustu (no_key 162.5, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 398.3 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 373.9 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- fail-shorts-render-tests -> HO-IMP-20261026-fail-shorts-render-tests (pending); model: gemini
