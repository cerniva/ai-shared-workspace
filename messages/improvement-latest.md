# improvement-bot raporu (2026-11-01, 2026W44)

Uretim: 2026-11-01T11:54:04+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 36

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 62 sn (maks 69, 16 kosu)
- improvement-bot: 62 sn (maks 65, 2 kosu)
- worker-orchestration-tests: 51 sn (maks 94, 31 kosu)
- En cok kirilan: takipci-denetci %67 (16/24)
- En uzun acik devir: HO-20261009-08 542.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 160.8 sa
- En uzun bekleyen bot PR: #158 518.6 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 62 sn (16 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 62 sn (2 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 51 sn (31 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %67 (16/24). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 160.8 saat dustu (no_key 160.8, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 542.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 518.6 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-codeql-code-scanning -> HO-IMP-20261101-slow-codeql-code-scanning (pending); model: gemini
