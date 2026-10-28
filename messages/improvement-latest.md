# improvement-bot raporu (2026-10-28, 2026W44)

Uretim: 2026-10-28T11:25:42+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 28

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 62 sn (maks 70, 36 kosu)
- shorts-render-tests: 59 sn (maks 502, 9 kosu)
- worker-orchestration-tests: 51 sn (maks 2063, 46 kosu)
- En cok kirilan: shorts-render-tests %44 (4/9)
- En uzun acik devir: HO-20261009-08 446.4 sa (open, auditor)
- En cok dusen saglayici: cerebras 163.3 sa
- En uzun bekleyen bot PR: #158 422.1 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 62 sn (36 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-render-tests' medyan 59 sn (9 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 51 sn (46 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'shorts-render-tests' basarisizlik orani %44 (4/9). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 163.3 saat dustu (no_key 163.3, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 446.4 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 422.1 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- provider-cerebras -> HO-IMP-20261028-provider-cerebras (pending); model: gemini
