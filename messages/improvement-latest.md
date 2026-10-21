# improvement-bot raporu (2026-10-21, 2026W43)

Uretim: 2026-10-21T05:51:54+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 10

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 64 sn (maks 67, 2 kosu)
- auto-merge-gate: 58 sn (maks 92, 44 kosu)
- shorts-render-tests: 56 sn (maks 64, 2 kosu)
- En cok kirilan: archive-heal %38 (10/26)
- En uzun acik devir: HO-20261009-08 272.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 167.8 sa
- En uzun bekleyen bot PR: #158 248.5 sa
- YAPAMADIM notlu devir: 18
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 64 sn (2 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 58 sn (44 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-render-tests' medyan 56 sn (2 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'archive-heal' basarisizlik orani %38 (10/26). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 167.8 saat dustu (no_key 167.8, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 272.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 248.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-auto-merge-gate -> HO-IMP-20261021-slow-auto-merge-gate (pending); model: yok (kural tabanli)
