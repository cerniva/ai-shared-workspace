# improvement-bot raporu (2026-11-09, 2026W46)

Uretim: 2026-11-09T14:01:46+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 45

## Darbogazlar

**En yavas 3 workflow (medyan):**
- auto-merge-gate: 173 sn (maks 1717, 32 kosu)
- CodeQL code scanning: 90 sn (maks 90, 1 kosu)
- improvement-bot: 60 sn (maks 116, 5 kosu)
- En cok kirilan: takipci-denetci %50 (6/12)
- En uzun acik devir: HO-20261009-08 737.0 sa (open, auditor)
- En cok dusen saglayici: cerebras 155.2 sa
- En uzun bekleyen bot PR: #158 712.7 sa
- YAPAMADIM notlu devir: 26
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'auto-merge-gate' medyan 173 sn (32 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 90 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'improvement-bot' medyan 60 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'takipci-denetci' basarisizlik orani %50 (6/12). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 155.2 saat dustu (no_key 155.2, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 737.0 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 712.7 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- fail-takipci-denetci -> HO-IMP-20261109-fail-takipci-denetci (pending); model: gemini
