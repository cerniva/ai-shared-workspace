# improvement-bot raporu (2026-10-27, 2026W44)

Uretim: 2026-10-27T10:41:29+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 26

## Darbogazlar

**En yavas 3 workflow (medyan):**
- research-learner: 85 sn (maks 85, 1 kosu)
- CodeQL code scanning: 61 sn (maks 87, 49 kosu)
- shorts-render-tests: 59 sn (maks 508, 25 kosu)
- En cok kirilan: shorts-render-tests %48 (12/25)
- En uzun acik devir: HO-20261009-08 421.7 sa (open, auditor)
- En cok dusen saglayici: cerebras 166.8 sa
- En uzun bekleyen bot PR: #158 397.4 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'research-learner' medyan 85 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 61 sn (49 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-render-tests' medyan 59 sn (25 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'shorts-render-tests' basarisizlik orani %48 (12/25). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 166.8 saat dustu (no_key 166.8, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 421.7 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 397.4 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-research-learner -> HO-IMP-20261027-slow-research-learner (pending); model: gemini
