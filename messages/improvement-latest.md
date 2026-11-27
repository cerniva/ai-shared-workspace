# improvement-bot raporu (2026-11-27, 2026W48)

Uretim: 2026-11-27T15:17:00+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 41

## Darbogazlar

**En yavas 3 workflow (medyan):**
- automation-runner: 76 sn (maks 113, 8 kosu)
- CodeQL code scanning: 74 sn (maks 90, 13 kosu)
- research-learner: 55 sn (maks 164, 5 kosu)
- En cok kirilan: takipci-denetci %35 (7/20)
- En uzun acik devir: HO-20261009-08 1170.3 sa (open, auditor)
- En cok dusen saglayici: cerebras 156.2 sa
- En uzun bekleyen bot PR: #158 1146.0 sa
- YAPAMADIM notlu devir: 33
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'automation-runner' medyan 76 sn (8 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 74 sn (13 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'research-learner' medyan 55 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %35 (7/20). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 156.2 saat dustu (no_key 156.2, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 1170.3 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 1146.0 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-automation-runner -> HO-IMP-20261127-slow-automation-runner (pending); model: gemini
