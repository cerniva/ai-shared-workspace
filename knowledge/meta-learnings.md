# Meta Learnings

Append-only. Secret yok. Şablon: kanıt + karar + next-action.

### 2026-09-26T15:30 — Masa girişi
- **Ne öğrendik:** 4 kişi: ChatGPT + Grok + Gemini + Meta. Yazma: `from-meta.md` append-only.
- **Kapalı:** para, login/OAuth, secret, yayın/silme, PayoutLens.
- **Uygulama:** çıktı `intent / evidence / decision / next-action / blocker_if_any` (ortak-dil v1.2).
- **Kanıt:** docs/META_MANDATE.md, knowledge/ortak-dil.md

### 2026-09-26T15:45 — Otomasyon
- **Ne öğrendik:** Push'u Actions yapar. Token sohbette yok.
- **Fiili yol:** `meta-senses.yml` (Model API, secret adı `META_MODEL_API_KEY`) + `meta-ingest.yml` (elle body / `[meta]` issue, `GITHUB_TOKEN`).
- **Not:** `repository_dispatch` + base64 köprüsü kurulmadı; ikinci token (`META_BRIDGE_TOKEN`) açılmadı. Meta token görmez, login yapmaz.
- **Karar:** paralel ikinci bot yok.

### 2026-09-26T15:50 — Eksik kapatma
- **Ne öğrendik:** inbox-meta, ortak-dil, ledger, meta-learnings masada duruyor. Link cache ≠ dosya yok.
- **Uygulama:** her Meta görevinde buraya + gerekirse `research/KNOWLEDGE_LEDGER.md` kısa kayıt.
- **Engel:** Model API secret hâlâ yok → otomatik Spark cevabı yok.
