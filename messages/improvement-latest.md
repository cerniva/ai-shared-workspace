# improvement-bot raporu (2026-10-14, 2026W42)

Uretim: 2026-10-14T05:51:01+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 7

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 64 sn (maks 68, 4 kosu)
- worker-orchestration-tests: 56 sn (maks 99, 16 kosu)
- auto-merge-gate: 50 sn (maks 87, 42 kosu)
- En cok kirilan: archive-heal %56 (14/25)
- En uzun acik devir: HO-20261009-08 104.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 100.7 sa
- En uzun bekleyen bot PR: #158 80.5 sa
- YAPAMADIM notlu devir: 6
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 64 sn (4 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 56 sn (16 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 50 sn (42 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'archive-heal' basarisizlik orani %56 (14/25). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 100.7 saat dustu (no_key 100.7, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 104.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 80.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-auto-merge-gate -> HO-IMP-20261014-slow-auto-merge-gate (pending); model: yok (kural tabanli)
