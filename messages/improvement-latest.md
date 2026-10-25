# improvement-bot raporu (2026-10-25, 2026W43)

Uretim: 2026-10-25T05:50:23+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 24

## Darbogazlar

**En yavas 3 workflow (medyan):**
- CodeQL code scanning: 70 sn (maks 100, 32 kosu)
- shorts-free-smoke-once: 66 sn (maks 72, 6 kosu)
- shorts-render-tests: 64 sn (maks 92, 8 kosu)
- En cok kirilan: takipci-denetci %13 (6/45)
- En uzun acik devir: HO-20261009-08 368.8 sa (open, auditor)
- En cok dusen saglayici: cerebras 167.8 sa
- En uzun bekleyen bot PR: #158 344.5 sa
- YAPAMADIM notlu devir: 24
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'CodeQL code scanning' medyan 70 sn (32 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-free-smoke-once' medyan 66 sn (6 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-render-tests' medyan 64 sn (8 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %13 (6/45). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 167.8 saat dustu (no_key 167.8, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 368.8 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 344.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-codeql-code-scanning -> HO-IMP-20261025-slow-codeql-code-scanning (pending); model: yok (kural tabanli)
