# improvement-bot raporu (2026-11-17, 2026W47)

Uretim: 2026-11-17T14:39:01+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 51

## Darbogazlar

**En yavas 3 workflow (medyan):**
- tinyfish-youtube-analytics: 235 sn (maks 235, 1 kosu)
- auto-merge-gate: 165 sn (maks 4349, 25 kosu)
- CodeQL code scanning: 85 sn (maks 85, 1 kosu)
- En cok kirilan: takipci-denetci %67 (8/12)
- En uzun acik devir: HO-20261009-08 929.7 sa (open, auditor)
- En cok dusen saglayici: cerebras 163.5 sa
- En uzun bekleyen bot PR: #158 905.3 sa
- YAPAMADIM notlu devir: 27
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'tinyfish-youtube-analytics' medyan 235 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 165 sn (25 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 85 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %67 (8/12). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 163.5 saat dustu (no_key 163.5, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 929.7 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 905.3 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-tinyfish-youtube-analytics -> HO-IMP-20261117-slow-tinyfish-youtube-analytics (pending); model: yok (kural tabanli)
