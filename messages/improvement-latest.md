# improvement-bot raporu (2026-11-16, 2026W47)

Uretim: 2026-11-16T13:47:06+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 50

## Darbogazlar

**En yavas 3 workflow (medyan):**
- auto-merge-gate: 151 sn (maks 4349, 31 kosu)
- CodeQL code scanning: 78 sn (maks 85, 2 kosu)
- research-learner: 74 sn (maks 121, 5 kosu)
- En cok kirilan: takipci-denetci %62 (8/13)
- En uzun acik devir: HO-20261009-08 904.8 sa (open, auditor)
- En cok dusen saglayici: cerebras 158.9 sa
- En uzun bekleyen bot PR: #158 880.5 sa
- YAPAMADIM notlu devir: 27
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'auto-merge-gate' medyan 151 sn (31 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 78 sn (2 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'research-learner' medyan 74 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %62 (8/13). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 158.9 saat dustu (no_key 158.9, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 904.8 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 880.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-auto-merge-gate -> HO-IMP-20261116-slow-auto-merge-gate (pending); model: gemini
