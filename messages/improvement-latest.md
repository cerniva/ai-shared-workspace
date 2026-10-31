# improvement-bot raporu (2026-10-31, 2026W44)

Uretim: 2026-10-31T10:58:48+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 35

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 63 sn (maks 69, 18 kosu)
- improvement-bot: 56 sn (maks 60, 2 kosu)
- worker-orchestration-tests: 51 sn (maks 105, 30 kosu)
- En cok kirilan: shorts-cdc-source-audit %100 (3/3)
- En uzun acik devir: HO-20261009-08 518.0 sa (open, auditor)
- En cok dusen saglayici: cerebras 164.8 sa
- En uzun bekleyen bot PR: #158 493.6 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 63 sn (18 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 56 sn (2 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 51 sn (30 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'shorts-cdc-source-audit' basarisizlik orani %100 (3/3). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 164.8 saat dustu (no_key 164.8, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 518.0 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 493.6 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-worker-orchestration-tests -> HO-IMP-20261031-slow-worker-orchestration-tests (pending); model: gemini
