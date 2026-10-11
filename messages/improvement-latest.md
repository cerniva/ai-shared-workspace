# improvement-bot raporu (2026-10-11, 2026W41)

Uretim: 2026-10-11T05:35:44+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 1

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 67 sn (maks 99, 17 kosu)
- worker-orchestration-tests: 54 sn (maks 77, 27 kosu)
- team-worker: 34 sn (maks 63, 60 kosu)
- En cok kirilan: takipci-denetci %58 (14/24)
- En uzun acik devir: HO-20261009-03 32.8 sa (claimed, grok)
- En cok dusen saglayici: cerebras 28.5 sa
- En uzun bekleyen bot PR: #158 8.3 sa
- YAPAMADIM notlu devir: 0
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 67 sn (17 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'worker-orchestration-tests' medyan 54 sn (27 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'team-worker' medyan 34 sn (60 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %58 (14/24). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 28.5 saat dustu (no_key 28.5, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-03 (grok, claimed) 32.8 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 8.3 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-codeql-code-scanning -> HO-IMP-20261011-slow-codeql-code-scanning (pending); model: yok (kural tabanli)
