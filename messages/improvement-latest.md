# improvement-bot raporu (2026-10-15, 2026W42)

Uretim: 2026-10-15T05:51:24+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 10

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 64 sn (maks 82, 11 kosu)
- worker-orchestration-tests: 54 sn (maks 72, 24 kosu)
- team-worker: 34 sn (maks 2427, 38 kosu)
- En cok kirilan: archive-heal %87 (20/23)
- En uzun acik devir: HO-20261009-08 128.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 124.7 sa
- En uzun bekleyen bot PR: #158 104.5 sa
- YAPAMADIM notlu devir: 9
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 64 sn (11 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 54 sn (24 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'team-worker' medyan 34 sn (38 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'archive-heal' basarisizlik orani %87 (20/23). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 124.7 saat dustu (no_key 124.7, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 128.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 104.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-team-worker -> HO-IMP-20261015-slow-team-worker (pending); model: yok (kural tabanli)
