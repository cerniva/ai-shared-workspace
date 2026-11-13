# improvement-bot raporu (2026-11-13, 2026W46)

Uretim: 2026-11-13T13:13:42+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 48

## Darbogazlar

**En yavas 3 workflow (medyan):**
- tinyfish-youtube-analytics: 143 sn (maks 143, 1 kosu)
- improvement-bot: 72 sn (maks 129, 4 kosu)
- CodeQL code scanning: 69 sn (maks 107, 8 kosu)
- En cok kirilan: takipci-denetci %29 (7/24)
- En uzun acik devir: HO-20261009-08 832.2 sa (open, auditor)
- En cok dusen saglayici: cerebras 160.9 sa
- En uzun bekleyen bot PR: #158 807.9 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'tinyfish-youtube-analytics' medyan 143 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 72 sn (4 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 69 sn (8 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %29 (7/24). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 160.9 saat dustu (no_key 160.9, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 832.2 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 807.9 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- provider-cerebras -> HO-IMP-20261113-provider-cerebras (pending); model: gemini
