# improvement-bot raporu (2026-11-18, 2026W47)

Uretim: 2026-11-18T14:15:58+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 51

## Darbogazlar

**En yavas 3 workflow (medyan):**
- knowledge-promotion-pr-gate: 1452 sn (maks 4350, 6 kosu)
- tinyfish-youtube-analytics: 235 sn (maks 235, 1 kosu)
- auto-merge-gate: 171 sn (maks 4349, 24 kosu)
- En cok kirilan: takipci-denetci %75 (9/12)
- En uzun acik devir: HO-20261009-08 953.3 sa (open, auditor)
- En cok dusen saglayici: cerebras 167.6 sa
- En uzun bekleyen bot PR: #158 928.9 sa
- YAPAMADIM notlu devir: 28
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'knowledge-promotion-pr-gate' medyan 1452 sn (6 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'tinyfish-youtube-analytics' medyan 235 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 171 sn (24 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %75 (9/12). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 167.6 saat dustu (no_key 167.6, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 953.3 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 928.9 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-knowledge-promotion-pr-gate -> HO-IMP-20261118-slow-knowledge-promotion-pr-gate (pending); model: yok (kural tabanli)
