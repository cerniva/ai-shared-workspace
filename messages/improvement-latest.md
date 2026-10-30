# improvement-bot raporu (2026-10-30, 2026W44)

Uretim: 2026-10-30T11:27:43+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 34

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 63 sn (maks 78, 24 kosu)
- improvement-bot: 51 sn (maks 51, 1 kosu)
- worker-orchestration-tests: 51 sn (maks 105, 32 kosu)
- En cok kirilan: shorts-cdc-source-audit %100 (3/3)
- En uzun acik devir: HO-20261009-08 494.5 sa (open, auditor)
- En cok dusen saglayici: cerebras 166.3 sa
- En uzun bekleyen bot PR: #158 470.1 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 63 sn (24 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 51 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 51 sn (32 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'shorts-cdc-source-audit' basarisizlik orani %100 (3/3). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 166.3 saat dustu (no_key 166.3, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 494.5 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 470.1 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- fail-shorts-cdc-source-audit -> HO-IMP-20261030-fail-shorts-cdc-source-audit (pending); model: gemini
