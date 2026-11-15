# improvement-bot raporu (2026-11-15, 2026W46)

Uretim: 2026-11-15T12:50:37+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 49

## Darbogazlar

**En yavas 3 workflow (medyan):**
- research-learner: 70 sn (maks 121, 5 kosu)
- CodeQL code scanning: 67 sn (maks 107, 7 kosu)
- worker-orchestration-tests: 63 sn (maks 4350, 29 kosu)
- En cok kirilan: takipci-denetci %39 (9/23)
- En uzun acik devir: HO-20261009-08 879.8 sa (open, auditor)
- En cok dusen saglayici: cerebras 160.7 sa
- En uzun bekleyen bot PR: #158 855.5 sa
- YAPAMADIM notlu devir: 27
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'research-learner' medyan 70 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 67 sn (7 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 63 sn (29 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %39 (9/23). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 160.7 saat dustu (no_key 160.7, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 879.8 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 855.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-codeql-code-scanning -> HO-IMP-20261115-slow-codeql-code-scanning (pending); model: gemini
