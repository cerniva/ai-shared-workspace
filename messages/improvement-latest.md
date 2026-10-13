# improvement-bot raporu (2026-10-13, 2026W42)

Uretim: 2026-10-13T05:39:36+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 5

## Darbogazlar

**En yavas 3 workflow (medyan):**
- research-learner: 92 sn (maks 93, 3 kosu)
- CodeQL code scanning: 85 sn (maks 88, 9 kosu)
- worker-orchestration-tests: 55 sn (maks 69, 21 kosu)
- En cok kirilan: takipci-denetci %50 (4/8)
- En uzun acik devir: HO-20261009-08 80.7 sa (open, auditor)
- En cok dusen saglayici: cerebras 76.6 sa
- En uzun bekleyen bot PR: #158 56.3 sa
- YAPAMADIM notlu devir: 4
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'research-learner' medyan 92 sn (3 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 85 sn (9 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 55 sn (21 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %50 (4/8). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 76.6 saat dustu (no_key 76.6, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 80.7 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 56.3 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-research-learner -> HO-IMP-20261013-slow-research-learner (pending); model: yok (kural tabanli)
