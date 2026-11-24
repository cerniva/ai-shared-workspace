# improvement-bot raporu (2026-11-24, 2026W48)

Uretim: 2026-11-24T15:59:10+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 56

## Darbogazlar

**En yavas 3 workflow (medyan):**
- auto-merge-gate: 187 sn (maks 3851, 29 kosu)
- improvement-bot: 131 sn (maks 178, 5 kosu)
- tinyfish-youtube-analytics: 117 sn (maks 117, 1 kosu)
- En cok kirilan: takipci-denetci %65 (13/20)
- En uzun acik devir: HO-20261009-08 1099.0 sa (open, auditor)
- En cok dusen saglayici: cerebras 152.2 sa
- En uzun bekleyen bot PR: #158 1074.7 sa
- YAPAMADIM notlu devir: 33
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'auto-merge-gate' medyan 187 sn (29 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 131 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'tinyfish-youtube-analytics' medyan 117 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %65 (13/20). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 152.2 saat dustu (no_key 152.2, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 1099.0 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 1074.7 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-tinyfish-youtube-analytics -> HO-IMP-20261124-slow-tinyfish-youtube-analytics (pending); model: gemini
