# improvement-bot raporu (2026-10-19, 2026W43)

Uretim: 2026-10-19T05:52:25+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 2

## Darbogazlar

**En yavas 3 workflow (medyan):**
- shorts-free-smoke-once: 66 sn (maks 73, 4 kosu)
- archive-heal: 62 sn (maks 113, 20 kosu)
- CodeQL code scanning: 61 sn (maks 88, 8 kosu)
- En cok kirilan: archive-heal %30 (6/20)
- En uzun acik devir: HO-20261009-08 224.9 sa (open, auditor)
- En cok dusen saglayici: cerebras 167.0 sa
- En uzun bekleyen bot PR: #158 200.5 sa
- YAPAMADIM notlu devir: 15
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'shorts-free-smoke-once' medyan 66 sn (4 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'archive-heal' medyan 62 sn (20 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 61 sn (8 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'archive-heal' basarisizlik orani %30 (6/20). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 167.0 saat dustu (no_key 167.0, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 224.9 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 200.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-shorts-free-smoke-once -> HO-IMP-20261019-slow-shorts-free-smoke-once (pending); model: gemini
