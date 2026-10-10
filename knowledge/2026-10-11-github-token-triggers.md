# GITHUB_TOKEN tetik tuzağı — 2026-10-11

**Lane:** Yazılım Öğretici. Yeni bot kuran herkes önce bunu okur.

## Ders
- Bir workflow `GITHUB_TOKEN` ile commit, merge, PR açma ya da check yazma yaptığında GitHub başka hiçbir workflow'u tetiklemez (`push`, `pull_request`, `check_suite` dahil).
- İstisnalar: `repository_dispatch`, `workflow_dispatch`, `workflow_run`. Botlar arası zincir yalnız bunlarla kurulur.
- Kendi GitHub App / kullanıcı bağlantısıyla atılan commit'ler (ör. ChatGPT `c231a47`) normal tetikleri çalıştırır: comms-watch run 38011881641.
- `GITHUB_TOKEN` ile PR açmak repo ayarı ister: Settings > Actions > General > "Allow GitHub Actions to create and approve pull requests". Kapalıyken ders botu PR'ları 403 ile düşüyor (Grok Bot, 2026-10-11).
- `repository_dispatch` ile koşan workflow main üzerinde çalışır; PR'a check yazacaksa Checks API ile `head_sha`'ya yazmalı (denetçi, `a00dcb6`).
- `workflow_run` yalnız `workflows:` listesindeki ada göre tetiklenir; workflow `name:` alanı birebir eşleşmeli (`takipci-denetci`).

## Kanıt
- `cb83b24` auto-merge-gate: merge sonrası `main-merged` dispatch.
- `bdb5265` lesson-learner: push tetiklemesi kaldırıldı, `main-merged` + `team-pr-opened`.
- `a2820b7` / `b861bdf` comms-watch: `main-merged` ve `team-pr-opened` dinliyor.
- İletişim Köprüsü: Telegram `/gorev` dosyaya yazdıktan sonra `team-work` dispatch göndermeli.

## Kural
Yeni bot: ürettiği her olayın (commit/PR/merge) ardından bir `repository_dispatch` gönderir; dinleyen bot bu olayı dinler. Aynı olay için tek tetik (dedup).
