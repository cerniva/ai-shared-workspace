# improvement-bot raporu (2026-10-20, 2026W43)

Uretim: 2026-10-20T05:52:10+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 6

## Darbogazlar

**En yavas 3 workflow (medyan):**
- tinyfish-youtube-analytics: 99 sn (maks 99, 1 kosu)
- shorts-render-tests: 66 sn (maks 69, 4 kosu)
- CodeQL code scanning: 63 sn (maks 88, 5 kosu)
- En cok kirilan: takipci-denetci %50 (9/18)
- En uzun acik devir: HO-20261009-08 248.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 167.0 sa
- En uzun bekleyen bot PR: #158 224.5 sa
- YAPAMADIM notlu devir: 16
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'tinyfish-youtube-analytics' medyan 99 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-render-tests' medyan 66 sn (4 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 63 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %50 (9/18). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 167.0 saat dustu (no_key 167.0, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 248.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 224.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-tinyfish-youtube-analytics -> HO-IMP-20261020-slow-tinyfish-youtube-analytics (pending); model: yok (kural tabanli)
