# improvement-bot raporu (2026-11-23, 2026W48)

Uretim: 2026-11-23T16:10:21+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 54

## Darbogazlar

**En yavas 3 workflow (medyan):**
- knowledge-promotion-pr-gate: 1726 sn (maks 3851, 8 kosu)
- auto-merge-gate: 196 sn (maks 3851, 29 kosu)
- improvement-bot: 126 sn (maks 133, 5 kosu)
- En cok kirilan: takipci-denetci %72 (13/18)
- En uzun acik devir: HO-20261009-08 1075.2 sa (open, auditor)
- En cok dusen saglayici: cerebras 156.5 sa
- En uzun bekleyen bot PR: #158 1050.8 sa
- YAPAMADIM notlu devir: 31
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'knowledge-promotion-pr-gate' medyan 1726 sn (8 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 196 sn (29 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 126 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %72 (13/18). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 156.5 saat dustu (no_key 156.5, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 1075.2 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 1050.8 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-auto-merge-gate -> HO-IMP-20261123-slow-auto-merge-gate (pending); model: yok (kural tabanli)
