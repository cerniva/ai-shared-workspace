# improvement-bot raporu (2026-10-23, 2026W43)

Uretim: 2026-10-23T05:53:00+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 20

## Darbogazlar

**En yavas 3 workflow (medyan):**
- archive-heal: 68 sn (maks 113, 19 kosu)
- auto-merge-gate: 67 sn (maks 3880, 52 kosu)
- CodeQL code scanning: 64 sn (maks 69, 4 kosu)
- En cok kirilan: takipci-denetci %43 (6/14)
- En uzun acik devir: HO-20261009-08 320.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 166.8 sa
- En uzun bekleyen bot PR: #158 296.6 sa
- YAPAMADIM notlu devir: 22
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'archive-heal' medyan 68 sn (19 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 67 sn (52 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 64 sn (4 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %43 (6/14). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 166.8 saat dustu (no_key 166.8, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 320.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 296.6 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-archive-heal -> HO-IMP-20261023-slow-archive-heal (pending); model: gemini
