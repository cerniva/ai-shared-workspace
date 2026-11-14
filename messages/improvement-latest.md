# improvement-bot raporu (2026-11-14, 2026W46)

Uretim: 2026-11-14T12:17:33+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 48

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 67 sn (maks 107, 7 kosu)
- research-learner: 62 sn (maks 121, 6 kosu)
- worker-orchestration-tests: 61 sn (maks 4350, 29 kosu)
- En cok kirilan: takipci-denetci %39 (9/23)
- En uzun acik devir: HO-20261009-08 855.3 sa (open, auditor)
- En cok dusen saglayici: cerebras 164.4 sa
- En uzun bekleyen bot PR: #158 831.0 sa
- YAPAMADIM notlu devir: 27
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 67 sn (7 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'research-learner' medyan 62 sn (6 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 61 sn (29 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %39 (9/23). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 164.4 saat dustu (no_key 164.4, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 855.3 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 831.0 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-research-learner -> HO-IMP-20261114-slow-research-learner (pending); model: gemini
