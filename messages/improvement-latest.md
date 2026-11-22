# improvement-bot raporu (2026-11-22, 2026W47)

Uretim: 2026-11-22T13:26:43+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 53

## Darbogazlar

**En yavas 3 workflow (medyan):**
- knowledge-promotion-pr-gate: 2304 sn (maks 3851, 8 kosu)
- auto-merge-gate: 206 sn (maks 3851, 28 kosu)
- improvement-bot: 90 sn (maks 133, 5 kosu)
- En cok kirilan: takipci-denetci %78 (14/18)
- En uzun acik devir: HO-20261009-08 1048.5 sa (open, auditor)
- En cok dusen saglayici: cerebras 162.2 sa
- En uzun bekleyen bot PR: #158 1024.1 sa
- YAPAMADIM notlu devir: 31
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'knowledge-promotion-pr-gate' medyan 2304 sn (8 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 206 sn (28 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 90 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %78 (14/18). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 162.2 saat dustu (no_key 162.2, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 1048.5 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 1024.1 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-improvement-bot -> HO-IMP-20261122-slow-improvement-bot (pending); model: yok (kural tabanli)
