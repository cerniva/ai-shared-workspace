# improvement-bot raporu (2026-11-03, 2026W45)

Uretim: 2026-11-03T12:52:26+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 38

## Darbogazlar

**En yavas 3 workflow (medyan):**
- tinyfish-youtube-analytics: 137 sn (maks 137, 1 kosu)
- CodeQL code scanning: 62 sn (maks 111, 10 kosu)
- improvement-bot: 58 sn (maks 65, 4 kosu)
- En cok kirilan: takipci-denetci %41 (7/17)
- En uzun acik devir: HO-20261009-08 591.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 162.2 sa
- En uzun bekleyen bot PR: #158 567.5 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'tinyfish-youtube-analytics' medyan 137 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 62 sn (10 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 58 sn (4 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %41 (7/17). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 162.2 saat dustu (no_key 162.2, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 591.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 567.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-tinyfish-youtube-analytics -> HO-IMP-20261103-slow-tinyfish-youtube-analytics (pending); model: gemini
