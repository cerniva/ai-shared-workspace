# improvement-bot raporu (2026-10-24, 2026W43)

Uretim: 2026-10-24T05:51:00+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 24

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 66 sn (maks 115, 40 kosu)
- worker-orchestration-tests: 56 sn (maks 2526, 50 kosu)
- shorts-render-tests: 54 sn (maks 2316, 20 kosu)
- En cok kirilan: shorts-render-tests %15 (3/20)
- En uzun acik devir: HO-20261009-08 344.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 167.7 sa
- En uzun bekleyen bot PR: #158 320.5 sa
- YAPAMADIM notlu devir: 22
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 66 sn (40 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 56 sn (50 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-render-tests' medyan 54 sn (20 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'shorts-render-tests' basarisizlik orani %15 (3/20). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 167.7 saat dustu (no_key 167.7, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 344.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 320.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-worker-orchestration-tests -> HO-IMP-20261024-slow-worker-orchestration-tests (pending); model: gemini
