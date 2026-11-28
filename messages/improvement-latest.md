# improvement-bot raporu (2026-11-28, 2026W48)

Uretim: 2026-11-28T14:19:56+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 42

## Darbogazlar

**En yavas 3 workflow (medyan):**
- research-learner: 83 sn (maks 164, 3 kosu)
- CodeQL code scanning: 74 sn (maks 89, 9 kosu)
- automation-runner: 50 sn (maks 113, 10 kosu)
- En cok kirilan: takipci-denetci %31 (5/16)
- En uzun acik devir: HO-20261009-08 1193.3 sa (open, auditor)
- En cok dusen saglayici: cerebras 160.9 sa
- En uzun bekleyen bot PR: #158 1169.0 sa
- YAPAMADIM notlu devir: 33
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'research-learner' medyan 83 sn (3 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 74 sn (9 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'automation-runner' medyan 50 sn (10 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %31 (5/16). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 160.9 saat dustu (no_key 160.9, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 1193.3 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 1169.0 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- yok (no_new_suggestion)
