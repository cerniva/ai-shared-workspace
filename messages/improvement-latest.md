# improvement-bot raporu (2026-10-18, 2026W42)

Uretim: 2026-10-18T05:47:45+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 4

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 83 sn (maks 130, 15 kosu)
- worker-orchestration-tests: 53 sn (maks 6301, 29 kosu)
- auto-merge-gate: 50 sn (maks 6301, 37 kosu)
- En cok kirilan: takipci-denetci %50 (2/4)
- En uzun acik devir: HO-20261009-08 200.8 sa (open, auditor)
- En cok dusen saglayici: cerebras 167.2 sa
- En uzun bekleyen bot PR: #158 176.5 sa
- YAPAMADIM notlu devir: 14
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 83 sn (15 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 53 sn (29 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 50 sn (37 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %50 (2/4). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 167.2 saat dustu (no_key 167.2, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 200.8 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 176.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-codeql-code-scanning -> HO-IMP-20261018-slow-codeql-code-scanning (pending); model: gemini
