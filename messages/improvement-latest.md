# improvement-bot raporu (2026-11-07, 2026W45)

Uretim: 2026-11-07T11:48:40+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 43

## Darbogazlar

**En yavas 3 workflow (medyan):**
- tinyfish-youtube-analytics: 137 sn (maks 137, 1 kosu)
- auto-merge-gate: 136 sn (maks 1717, 53 kosu)
- CodeQL code scanning: 64 sn (maks 111, 4 kosu)
- En cok kirilan: takipci-denetci %38 (6/16)
- En uzun acik devir: HO-20261009-08 686.8 sa (open, auditor)
- En cok dusen saglayici: cerebras 159.8 sa
- En uzun bekleyen bot PR: #158 662.5 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'tinyfish-youtube-analytics' medyan 137 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 136 sn (53 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 64 sn (4 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %38 (6/16). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 159.8 saat dustu (no_key 159.8, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 686.8 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 662.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-auto-merge-gate -> HO-IMP-20261107-slow-auto-merge-gate (pending); model: gemini
