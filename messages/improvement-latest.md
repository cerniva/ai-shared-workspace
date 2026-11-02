# improvement-bot raporu (2026-11-02, 2026W45)

Uretim: 2026-11-02T13:38:42+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 37

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 63 sn (maks 111, 11 kosu)
- improvement-bot: 60 sn (maks 65, 3 kosu)
- worker-orchestration-tests: 51 sn (maks 67, 27 kosu)
- En cok kirilan: takipci-denetci %50 (8/16)
- En uzun acik devir: HO-20261009-08 568.7 sa (open, auditor)
- En cok dusen saglayici: cerebras 163.7 sa
- En uzun bekleyen bot PR: #158 544.3 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 63 sn (11 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 60 sn (3 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 51 sn (27 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %50 (8/16). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 163.7 saat dustu (no_key 163.7, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 568.7 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 544.3 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- fail-takipci-denetci -> HO-IMP-20261102-fail-takipci-denetci (pending); model: gemini
