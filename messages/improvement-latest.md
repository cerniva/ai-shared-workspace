# improvement-bot raporu (2026-10-29, 2026W44)

Uretim: 2026-10-29T11:36:09+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 31

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 64 sn (maks 92, 33 kosu)
- worker-orchestration-tests: 53 sn (maks 127, 39 kosu)
- improvement-bot: 49 sn (maks 49, 1 kosu)
- En cok kirilan: takipci-denetci %37 (14/38)
- En uzun acik devir: HO-20261009-08 470.6 sa (open, auditor)
- En cok dusen saglayici: cerebras 162.1 sa
- En uzun bekleyen bot PR: #158 446.3 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 64 sn (33 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 53 sn (39 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 49 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %37 (14/38). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 162.1 saat dustu (no_key 162.1, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 470.6 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 446.3 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-improvement-bot -> HO-IMP-20261029-slow-improvement-bot (pending); model: gemini
