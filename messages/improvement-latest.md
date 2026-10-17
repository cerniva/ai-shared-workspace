# improvement-bot raporu (2026-10-17, 2026W42)

Uretim: 2026-10-17T05:47:51+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 8

## Darbogazlar

**En yavas 3 workflow (medyan):**
- github_actions in /. - Update #1632471704: 119 sn (maks 119, 1 kosu)
- auto-merge-gate: 91 sn (maks 1494, 33 kosu)
- CodeQL code scanning: 74 sn (maks 82, 5 kosu)
- En cok kirilan: archive-heal %85 (51/60)
- En uzun acik devir: HO-20261009-08 176.8 sa (open, auditor)
- En cok dusen saglayici: cerebras 167.1 sa
- En uzun bekleyen bot PR: #158 152.5 sa
- YAPAMADIM notlu devir: 11
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'github_actions in /. - Update #1632471704' medyan 119 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'auto-merge-gate' medyan 91 sn (33 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 74 sn (5 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'archive-heal' basarisizlik orani %85 (51/60). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 167.1 saat dustu (no_key 167.1, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-08 (auditor, open) 176.8 saattir acik; sahibine hatirlat veya kapat.
- (review) bot PR #158 (bot/telegram-model-fallback-20261011) 152.5 saattir bekliyor; incele/birlestir/kapat.

## Bu kosunun team-worker isi

- slow-github-actions-in-update-1632471704 -> HO-IMP-20261017-slow-github-actions-in-update-1632471704 (pending); model: yok (kural tabanli)
