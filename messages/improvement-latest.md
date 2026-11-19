# improvement-bot raporu (2026-11-19, 2026W47)

Uretim: 2026-11-19T14:31:08+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 51

## Darbogazlar

**En yavas 3 workflow (medyan):**
- knowledge-promotion-pr-gate: 1452 sn (maks 3209, 6 kosu)
- tinyfish-youtube-analytics: 235 sn (maks 235, 1 kosu)
- auto-merge-gate: 180 sn (maks 3209, 24 kosu)
- En cok kirilan: takipci-denetci %75 (9/12)
- En uzun acik devir: HO-20261009-08 977.5 sa (open, auditor)
- En cok dusen saglayici: cerebras 162.1 sa
- En uzun bekleyen bot PR: #158 953.2 sa
- YAPAMADIM notlu devir: 29
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'knowledge-promotion-pr-gate' medyan 1452 sn (6 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'tinyfish-youtube-analytics' medyan 235 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 180 sn (24 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %75 (9/12). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 162.1 saat dustu (no_key 162.1, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 977.5 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 953.2 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- fail-takipci-denetci -> HO-IMP-20261119-fail-takipci-denetci (pending); model: yok (kural tabanli)
