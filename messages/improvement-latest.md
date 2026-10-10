# improvement-bot raporu (2026-10-10, 2026W41)

Uretim: 2026-10-10T05:35:10+00:00 | pencere: 7 gun | kosu: 1000 | bot PR: 0

## Darbogazlar

**En yavas 3 workflow (medyan):**
- github_actions in /. - Update #1620214326: 120 sn (maks 120, 1 kosu)
- CodeQL code scanning: 83 sn (maks 104, 59 kosu)
- shorts-render-tests: 55 sn (maks 106, 7 kosu)
- En cok kirilan: team-worker %67 (33/49)
- En uzun acik devir: HO-20261009-03 8.8 sa (claimed, grok)
- En cok dusen saglayici: cerebras 4.5 sa
- Acik bot/ PR: yok
- YAPAMADIM notlu devir: 0
- Inaktiflikten kapanan schedule'li workflow: yok

## Oneriler

- (speedup) 'github_actions in /. - Update #1620214326' medyan 120 sn (1 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'CodeQL code scanning' medyan 83 sn (59 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (speedup) 'shorts-render-tests' medyan 55 sn (7 kosu). Pip/apt adimlarina actions/cache ekle, gereksiz adimlari paths filtresiyle atla, bagimsiz test adimlarini paralel job'a bol.
- (reliability) 'team-worker' basarisizlik orani %67 (33/49). Son kirik kosularin logundaki ilk hatayi duzelt; flaky adima retry/timeout ekle.
- (provider) 'cerebras' 7 gunde 4.5 saat dustu (no_key 4.5, billing 0.0, quota 0.0). Fallback sirasinda geri al veya anahtar/kota duzelene kadar zincirden cikar.
- (handoff) HO-20261009-03 (grok, claimed) 8.8 saattir acik; sahibine hatirlat veya kapat.

## Bu kosunun team-worker isi

- slow-github-actions-in-update-1620214326 -> HO-IMP-20261010-slow-github-actions-in-update-1620214326 (pending); model: yok (kural tabanli)
