# improvement-bot raporu (2026-11-21, 2026W47)

Uretim: 2026-11-21T13:33:49+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 51

## Darbogazlar

**En yavas 3 workflow (medyan):**
- knowledge-promotion-pr-gate: 2880 sn (maks 3851, 7 kosu)
- tinyfish-youtube-analytics: 235 sn (maks 235, 1 kosu)
- auto-merge-gate: 219 sn (maks 3851, 26 kosu)
- En cok kirilan: knowledge-promotion-pr-gate %86 (6/7)
- En uzun acik devir: HO-20261009-08 1024.6 sa (open, auditor)
- En cok dusen saglayici: cerebras 160.7 sa
- En uzun bekleyen bot PR: #158 1000.2 sa
- YAPAMADIM notlu devir: 31
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'knowledge-promotion-pr-gate' medyan 2880 sn (7 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'tinyfish-youtube-analytics' medyan 235 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 219 sn (26 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'knowledge-promotion-pr-gate' basarisizlik orani %86 (6/7). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 160.7 saat dustu (no_key 160.7, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 1024.6 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 1000.2 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- fail-knowledge-promotion-pr-gate -> HO-IMP-20261121-fail-knowledge-promotion-pr-gate (pending); model: yok (kural tabanli)
