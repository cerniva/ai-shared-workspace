# improvement-bot raporu (2026-11-20, 2026W47)

Uretim: 2026-11-20T14:08:26+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 51

## Darbogazlar

**En yavas 3 workflow (medyan):**
- knowledge-promotion-pr-gate: 1727 sn (maks 3209, 7 kosu)
- tinyfish-youtube-analytics: 235 sn (maks 235, 1 kosu)
- auto-merge-gate: 203 sn (maks 3209, 27 kosu)
- En cok kirilan: takipci-denetci %75 (12/16)
- En uzun acik devir: HO-20261009-08 1001.1 sa (open, auditor)
- En cok dusen saglayici: cerebras 163.2 sa
- En uzun bekleyen bot PR: #158 976.8 sa
- YAPAMADIM notlu devir: 30
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'knowledge-promotion-pr-gate' medyan 1727 sn (7 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'tinyfish-youtube-analytics' medyan 235 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 203 sn (27 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %75 (12/16). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 163.2 saat dustu (no_key 163.2, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 1001.1 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 976.8 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- provider-cerebras -> HO-IMP-20261120-provider-cerebras (pending); model: yok (kural tabanli)
