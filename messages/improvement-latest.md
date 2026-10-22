# improvement-bot raporu (2026-10-22, 2026W43)

Uretim: 2026-10-22T05:51:38+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 15

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 64 sn (maks 67, 4 kosu)
- auto-merge-gate: 61 sn (maks 102, 51 kosu)
- shorts-render-tests: 57 sn (maks 64, 3 kosu)
- En cok kirilan: archive-heal %50 (10/20)
- En uzun acik devir: HO-20261009-08 296.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 167.8 sa
- En uzun bekleyen bot PR: #158 272.5 sa
- YAPAMADIM notlu devir: 21
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 64 sn (4 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 61 sn (51 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-render-tests' medyan 57 sn (3 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'archive-heal' basarisizlik orani %50 (10/20). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 167.8 saat dustu (no_key 167.8, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 296.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 272.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-shorts-render-tests -> HO-IMP-20261022-slow-shorts-render-tests (pending); model: yok (kural tabanli)
