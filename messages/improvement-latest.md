# improvement-bot raporu (2026-11-08, 2026W45)

Uretim: 2026-11-08T11:59:37+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 44

## Darbogazlar

**En yavas 3 workflow (medyan):**
- auto-merge-gate: 160 sn (maks 1717, 47 kosu)
- tinyfish-youtube-analytics: 137 sn (maks 137, 1 kosu)
- CodeQL code scanning: 65 sn (maks 111, 3 kosu)
- En cok kirilan: takipci-denetci %40 (6/15)
- En uzun acik devir: HO-20261009-08 711.0 sa (open, auditor)
- En cok dusen saglayici: cerebras 165.0 sa
- En uzun bekleyen bot PR: #158 686.7 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'auto-merge-gate' medyan 160 sn (47 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'tinyfish-youtube-analytics' medyan 137 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 65 sn (3 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %40 (6/15). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 165.0 saat dustu (no_key 165.0, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 711.0 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 686.7 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-codeql-code-scanning -> HO-IMP-20261108-slow-codeql-code-scanning (pending); model: gemini
