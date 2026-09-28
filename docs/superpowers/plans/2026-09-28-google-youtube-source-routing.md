# Google + YouTube Source Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Google + YouTube kaynaklarını ortak bilgi katmanına güven sınırlarıyla eklemek, görev dağılımını genişletmek ve aktif otomasyonların aynı yönlendirme/dedup kurallarını kullanmasını sağlamak.

**Architecture:** Mevcut `knowledge/source_catalog.json` ve `knowledge/RESEARCH_ROUTER.md` kaynak kanonu olarak korunacak; görev sahipliği `tasks/active.json`, canlı doğrulanmış bağlantı durumu `state/now.json`, kullanıcı-side kararlar `state/cross_chat_sync.json` içinde tutulacak. Google keşif katmanı; YouTube/vidIQ/Metricool ise ayrı araştırma, owned-analytics ve yayın rolleri olarak tanımlanacak. Otomasyonlar repo durumunu okuyup yalnız kendi kuyruğuna düşen işi yapacak.

**Tech Stack:** JSON state files, Python bridge/validation scripts, GitHub Actions/CI, TinyFish Search/Browser, vidIQ, Metricool, ChatGPT Automations.

**Spec:** `docs/superpowers/specs/2026-09-28-google-youtube-source-routing-design.md`

## Global Constraints

- PayoutLens dosyaları, görevleri ve kapsamı değiştirilmeyecek.
- Google arama sonucu/snippet tek başına doğrulanmış kanıt sayılmayacak.
- YouTube creator içeriği tek başına finansal/teknik gerçek sayılmayacak.
- `verified-connected` yalnız gerçek tool/service read-back ile verilecek.
- YouTube Studio Browser Context Profile yalnız başarılı Studio run/read ile verified yapılacak.
- Direct YouTube OAuth `invalid_grant` blocker'ı Metricool çalışıyor diye silinmeyecek.
- Login/2FA/payment/legal/sensitive permission/irreversible action kullanıcı kapısı olarak kalacak.
- Free-first yaklaşım korunacak; sırf bağlantı doğrulamak için ücretli/credit harcayan çağrı yapılmayacak.
- Secret/token/password/cookie/session değerleri repo, log veya automation promptuna yazılmayacak.
- Aynı araştırma Google, YouTube ve vidIQ tarafından gereksiz yere üç kez tekrarlanmayacak.

## Review Focus

- Arama sonucu keşif sinyali ile doğrulanmış kaynak ayrımı korunmalı; kritik iddia resmi/birincil kaynağa yükseltilmeli.
- Browser profile kurulmuş olması `verified-connected` sayılmamalı; runtime kanıtı yoksa `user_reported`/`unverified` kalmalı.
- Metricool/vidIQ başarısı direct YouTube OAuth `invalid_grant` durumunu örtmemeli.
- Canonical/tool source kimlikleri duplicate olmamalı; bridge `find -> add-if-new -> read-back -> validate` akışı korunmalı.
- Automation promptları güncellenirken schedule, enabled state ve mevcut güvenlik kapıları değişmemeli.

---

### Task 1: Kaynak yönlendirme politikasını ve machine catalog'u genişlet

**Files:**
- Modify: `knowledge/RESEARCH_ROUTER.md`
- Modify: `knowledge/source_catalog.json`
- Validate: `scripts/knowledge_bridge.py`
- Regression: `tests/test_knowledge_bridge.py`

**Interfaces:**
- Consumes: `knowledge/source_catalog.json` schema v1; `tool:<id>` canonical desteği.
- Produces: Google/YouTube/vidIQ/Metricool kaynak rollerinin ortak katalog + human-readable router eşleşmesi.

- [ ] **Step 1: Mevcut canonical kaynakları duplicate açısından kontrol et**

Run:
```bash
python3 scripts/knowledge_bridge.py validate
python3 scripts/knowledge_bridge.py find tool:tinyfish-search || true
python3 scripts/knowledge_bridge.py find tool:vidiq || true
python3 scripts/knowledge_bridge.py find tool:metricool-youtube || true
python3 scripts/knowledge_bridge.py find https://www.google.com/ || true
python3 scripts/knowledge_bridge.py find https://www.youtube.com/ || true
```
Expected: catalog valid; var olan kaynaklar yeniden eklenmez.

- [ ] **Step 2: `knowledge/RESEARCH_ROUTER.md` routing bölümünü güncelle**

Exact policy:
- Google/TinyFish Search = keşif ve resmi sayfa bulma; snippet kanıt değil.
- YouTube = official/platform docs + public format/hook/competitor observation.
- vidIQ = YouTube keyword/trend/outlier/competitor/owned analytics yardımcı kaynağı.
- Metricool = owned-channel scheduling/publishing/analytics source.
- Existing project knowledge remains first dedup check before external research.
- Finance: YouTube creator content is opinion/learning only unless independently verified.

- [ ] **Step 3: Kaynakları bridge üzerinden ekle; erişim durumunu runtime kanıtına göre seç**

Use these canonical IDs/names:
- `tool:tinyfish-search` — `TinyFish Search`
- `https://www.google.com/` — `Google Search discovery surface`
- `https://www.youtube.com/` — `YouTube public content surface`
- `tool:vidiq` — `vidIQ YouTube research and analytics`
- `tool:metricool-youtube` — `Metricool YouTube publishing and analytics`

Rules:
- public surface successfully opened/searched => `verified-public`.
- connected tool returns account/channel data => `verified-connected`.
- installed/setup but no read-back => `unverified`.
- `evidence_tier` for search/public creator discovery = `secondary`; official YouTube Help URLs remain `official`.

- [ ] **Step 4: Validate catalog and regression tests**

Run:
```bash
python3 scripts/knowledge_bridge.py validate
python3 -m unittest tests.test_knowledge_bridge -v
```
Expected: PASS; no duplicate canonical/source_id.

- [ ] **Step 5: Commit Task 1**

```bash
git add knowledge/RESEARCH_ROUTER.md knowledge/source_catalog.json
git commit -m "docs: route google and youtube research sources"
```

---

### Task 2: Ortak görev dağılımını ve cross-chat kararını kalıcılaştır

**Files:**
- Modify: `tasks/active.json`
- Modify: `state/cross_chat_sync.json`
- Modify: `state/now.json`
- Validate: `scripts/desk_context.py`
- Regression: `tests/test_desk_context.py`

**Interfaces:**
- Consumes: source roles from Task 1.
- Produces: CORE görevlerinin ayrıntılı worker/backup rolleri ve yalnız doğrulanmış live connection state.

- [ ] **Step 1: `state/cross_chat_sync.json` içine yeni confirmed user decision ekle**

Add one new delta id: `user-20260928-google-youtube-source-routing`.
Fact: Google + YouTube kaynak havuzuna dahil edilecek; TinyFish/vidIQ/Metricool görevleri ayrıştırılacak; duplicate research engellenecek.
Do not store account email, profile cookies, tokens or IDs that are not needed.

- [ ] **Step 2: `tasks/active.json` CORE notlarını genişlet**

Required role mapping:
- CORE-01: ChatGPT orchestrator; TinyFish Google/web discovery; Gemini research fallback; Grok red-team; source catalog mandatory dedup.
- CORE-02: Google/news discovery allowed; YouTube only official channels/opinion layer; primary finance sources remain authoritative.
- CORE-03: Google/TinyFish discovery -> YouTube/vidIQ trend/outlier/competitor -> Metricool/owned analytics -> free-first production -> QC -> Metricool/authorized publish -> read-back -> 24-48h learning.
- CORE-04: Google/SEO demand discovery -> commerce validation -> Shopify/Gumroad draft/read-back; payments remain gated.
- CORE-05: live state/CI -> Google/official docs/TinyFish solution discovery -> safe delta -> tests/CI/read-back.

Keep `max_persistent_tasks` unchanged and do not create duplicate standing CORE tasks.

- [ ] **Step 3: `state/now.json` routing/health fields güncelle**

Add only runtime-proven statements:
- `tinyfish` remains primary web worker if live.
- Metricool YouTube status only `verified-connected` after `getBrandSettings` confirms YouTube data.
- vidIQ only `verified-connected` after `vidiq_user_channels` returns owned channel(s).
- Google/YouTube browser profiles remain `setup-unverified` unless a successful profile-backed run/read is performed.
- preserve `youtube-oauth-invalid-grant` blocker until direct OAuth test succeeds.

- [ ] **Step 4: JSON parse + desk health doğrulaması**

Run:
```bash
python3 -m json.tool tasks/active.json >/dev/null
python3 -m json.tool state/now.json >/dev/null
python3 -m json.tool state/cross_chat_sync.json >/dev/null
python3 scripts/desk_context.py status
python3 -m unittest tests.test_desk_context -v
```
Expected: all parse; desk context reports valid knowledge bridge; no PayoutLens changes.

- [ ] **Step 5: Commit Task 2**

```bash
git add tasks/active.json state/now.json state/cross_chat_sync.json
git commit -m "chore: expand source-aware task routing"
```

---

### Task 3: Ücretsiz/low-cost bağlantı read-back'lerini yap ve state'i yalnız kanıtla yükselt

**Files:**
- Modify only if evidence changes: `state/now.json`, `knowledge/source_catalog.json`

**Interfaces:**
- Consumes: connected plugin/tool accounts.
- Produces: evidence-backed `verified-connected` / `verified-public` statuses.

- [ ] **Step 1: Metricool YouTube bağlantısını ücretsiz read ile doğrula**

Call `Metricool.getBrandSettings()`.
Expected: brand record contains `networksData.youtubeData` for the owned channel. If absent, do not mark connected.

- [ ] **Step 2: vidIQ owned-channel bağlantısını zero-credit read ile doğrula**

Call `vidiq.vidiq_user_channels()`.
Expected: at least one authorized YouTube channel. If empty, record unverified/not-connected; do not spend credits on channel stats just to verify.

- [ ] **Step 3: TinyFish Search'i düşük maliyetli discovery probe ile doğrula**

Call TinyFish Search with an official YouTube-help query, e.g. `site:support.google.com/youtube Shorts monetization official`.
Expected: search completes and returns official YouTube/Google results. This verifies the search worker, not a logged-in Google profile.

- [ ] **Step 4: Google/YouTube Browser Context Profile için fail-safe davran**

If a default/specific Browser Context Profile is available without asking for credentials, perform one read-only profile-backed navigation to `https://studio.youtube.com` and verify that Studio is authenticated. If this would consume paid credits solely for a cosmetic status check, skip it and keep `setup-unverified` until the next real Studio task.

Never ask for password/token in chat.

- [ ] **Step 5: Evidence-dependent state/catalog write and read-back**

Only promote the tools that passed. Re-run:
```bash
python3 scripts/knowledge_bridge.py validate
python3 -m json.tool state/now.json >/dev/null
```

- [ ] **Step 6: Commit Task 3 if repo state changed**

```bash
git add state/now.json knowledge/source_catalog.json
git commit -m "chore: record verified youtube research connections"
```

---

### Task 4: Aktif otomasyon promptlarını görev kuyruğuna göre ayrıştır

**Files:**
- External config only: ChatGPT Automations

**Interfaces:**
- Consumes: Task 1-3 routing contract.
- Produces: enabled automations with unchanged schedule/timing mode but expanded source-aware prompts.

Automation IDs to update by prompt only:
- `6aba455b923481919384e4920acf6ad4` — Email Monitor
- `6aba4441fc6481919df10375c8935f8c` — Bilgi Kütüphanesi
- `6aba4412dc808191becd88cf0f1a31d3` — Finans
- `6aba442b4bfc81918f590741da715067` — Video, Shopify ve Sistem Geliştirmeleri
- `6aba7d0cb8408191a5c9a7a4c17cc1b0` — Sistem Kaynak Araştırması

- [ ] **Step 1: Bilgi Kütüphanesi promptuna merkezi source routing ekle**

Must say: read shared catalog first; Google/TinyFish for discovery; YouTube/vidIQ/Metricool as separate content/analytics roles; canonical dedup; add only new decision value.

- [ ] **Step 2: Video/Shopify/Sistem promptunu üç alt kuyruk olarak netleştir**

Video queue exact order:
`shared-state/catalog -> Google/TinyFish discovery -> YouTube/vidIQ -> owned analytics -> free-first production -> QC -> authorized publish -> read-back -> learning`.

Commerce queue:
`catalog -> Google/SEO demand -> validation -> asset -> Shopify/Gumroad draft/read-back -> payment-gated publish`.

System queue:
`live state/CI -> official docs/Google/TinyFish -> safe fix -> test/CI/read-back`.

- [ ] **Step 3: Finans promptuna YouTube güven sınırını ekle**

YouTube creator content = opinion/learning layer only; official institution/company channels can be primary for their own statements; market facts still require primary/financial data verification.

- [ ] **Step 4: Email Monitor promptuna plan-router davranışı ekle**

Route new mail signal to the relevant plan and verify against live service state; do not turn stale mail into an open blocker.

- [ ] **Step 5: Sistem Kaynak Araştırması promptunu dar teknik feeder olarak tut**

Only research unresolved technical gaps and write reusable sources to the shared catalog; do not duplicate the combined plan's execution queue.

- [ ] **Step 6: Read-back automations and verify invariants**

Use `automations.peek()` after updates.
Expected for all five:
- `is_enabled` unchanged (`true`)
- existing hourly schedule unchanged
- timing mode unchanged
- prompts include source routing/dedup rules
- no secrets/credentials/profile cookies included

---

### Task 5: Branch verification, review and integration

**Files:**
- All files changed by Tasks 1-3
- External automation read-back from Task 4

**Interfaces:**
- Consumes: completed prior tasks.
- Produces: one reviewable PR with evidence summary.

- [ ] **Step 1: Run focused test suite**

Run:
```bash
python3 -m unittest tests.test_knowledge_bridge tests.test_learning_bridge tests.test_desk_context -v
python3 scripts/knowledge_bridge.py validate
python3 scripts/learning_bridge.py validate
python3 scripts/desk_context.py status
```
Expected: PASS / VALID; no bridge errors.

- [ ] **Step 2: Verify protected scope**

Run:
```bash
git diff --name-only main...HEAD
```
Expected: no PayoutLens path; no secret/env files; only approved docs/knowledge/state/tasks changes.

- [ ] **Step 3: Check the direct OAuth blocker is still represented**

Inspect `state/now.json`.
Expected: `youtube-oauth-invalid-grant` remains until a separate successful direct OAuth test proves resolution.

- [ ] **Step 4: Create/update PR**

PR title: `Expand Google and YouTube source routing`
PR body must summarize:
- source taxonomy added
- verified vs setup-only connections
- expanded CORE task distribution
- automation prompt changes and read-back
- tests/validation results
- PayoutLens untouched

- [ ] **Step 5: Review and merge only after checks pass**

Use the repository's normal review/CI flow. If another writer changed `source_catalog.json`, `tasks/active.json`, or `state/now.json`, re-read current main and reconcile; do not force overwrite.
