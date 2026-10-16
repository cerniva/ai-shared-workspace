# improvement-bot raporu (2026-10-16, 2026W42)

Uretim: 2026-10-16T05:50:20+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 11

## Darbogazlar

**En yavas 3 workflow (medyan):**
- auto-merge-gate: 103 sn (maks 133, 29 kosu)
- worker-orchestration-tests: 56 sn (maks 71, 15 kosu)
- improvement-bot: 37 sn (maks 37, 1 kosu)
- En cok kirilan: archive-heal %100 (33/33)
- En uzun acik devir: HO-20261009-08 152.8 sa (open, auditor)
- En cok dusen saglayici: cerebras 148.7 sa
- En uzun bekleyen bot PR: #158 128.5 sa
- YAPAMADIM notlu devir: 10
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'auto-merge-gate' medyan 103 sn (29 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 56 sn (15 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 37 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'archive-heal' basarisizlik orani %100 (33/33). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 148.7 saat dustu (no_key 148.7, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 152.8 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 128.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-improvement-bot -> HO-IMP-20261016-slow-improvement-bot (pending); model: yok (kural tabanli)
