# improvement-bot raporu (2026-10-12, 2026W42)

Uretim: 2026-10-12T05:38:56+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 3

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 86 sn (maks 92, 14 kosu)
- worker-orchestration-tests: 50 sn (maks 77, 22 kosu)
- auto-merge-gate: 46 sn (maks 77, 46 kosu)
- En cok kirilan: takipci-denetci %43 (3/7)
- En uzun acik devir: HO-20261009-08 56.7 sa (open, auditor)
- En cok dusen saglayici: cerebras 52.5 sa
- En uzun bekleyen bot PR: #158 32.3 sa
- YAPAMADIM notlu devir: 2
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 86 sn (14 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 50 sn (22 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 46 sn (46 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %43 (3/7). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 52.5 saat dustu (no_key 52.5, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 56.7 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 32.3 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-worker-orchestration-tests -> HO-IMP-20261012-slow-worker-orchestration-tests (pending); model: yok (kural tabanli)
