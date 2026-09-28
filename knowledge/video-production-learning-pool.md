# Video Production Learning Pool

Status: active shared knowledge
Updated: 2026-09-28
Scope: YouTube Shorts and reusable production lessons for scripting, editing, visuals, audio, packaging, publishing and analytics.

## Purpose
This is the shared human-readable production knowledge pool. Video/Shopify, Bilgi Kütüphanesi, Sistem Geliştirmeleri and any future production automation should read this file before repeating research or making a production decision. Use only relevant lessons; do not force video lessons into unrelated finance decisions.

Machine-readable canonical sources and durable learnings remain in `knowledge/source_catalog.json` and `knowledge/learning_ledger.json`. When execution access is available, new reusable lessons should also be written through `scripts/knowledge_bridge.py` and `scripts/learning_bridge.py` and read back/validated before claiming that machine sync is complete.

## Research order — cost first
1. Public YouTube metadata/search results.
2. Transcript/captions.
3. Comments and related-video patterns when useful.
4. Channel/video analytics for owned content.
5. Expensive scene-by-scene visual analysis only for a small number of unusually strong/weak examples or when transcript/metadata cannot answer the production question.

Do not spend credits watching every candidate. First filter cheaply, then deepen only on the highest-value examples.

## External YouTube observations — 2026-09-28

### Observation VP-001 — fast question → answer → conflict → resolution
Source: https://www.youtube.com/watch?v=I_DaRXgttkc
Observed public metadata at research time: 35 s; about 170M views.
Transcript structure:
- 0:00 direct curiosity question: why ants walk in a line.
- ~0:03–0:13 core explanation arrives quickly.
- ~0:18 a simple conflict/choice is introduced.
- ~0:20–0:30 correction + value/payoff.
- ~0:30–0:33 clean resolution.

Reusable hypothesis, not a causal claim: for factual/educational Shorts, test a concrete question in the first second, deliver the promised answer early, then add a small conflict/surprise/choice before a clear resolution. Measure chose-to-view, first-seconds retention, average view duration and rewatch behavior before keeping the pattern.

### Observation VP-002 — huge views can coexist with monetization/originality risk
Discovery sample: https://www.youtube.com/watch?v=PBhWlr3nMBY
Observed public metadata at research time: AI fruit/ASMR packaging, about 96M views, 2:16 duration. The same search surface showed several closely similar AI fruit-baby/satisfying concepts across different channels.

Reusable decision: treat repeated AI-satisfying concepts as demand/packaging evidence only. Do not clone or mass-produce near-duplicate concepts merely because the view counts are high. Before production, apply the YouTube originality/inauthentic/reused-content monetization gate and require meaningful original scripting, structure, visual treatment or commentary.

### Observation VP-003 — packaging patterns worth testing, not copying
High-view public examples repeatedly use:
- binary curiosity framing such as “Cute or Creepy?”;
- an immediately understandable visual noun in the title;
- a strong sensory promise such as satisfying/ASMR;
- short, concrete wording rather than abstract topic labels.

Reusable hypothesis: test titles/hooks with one clear curiosity contrast + one concrete visual object + one payoff. Do not assume this is universally causal; validate against our own channel data.

### Official rule VP-004 — separate exposure views from engaged/qualified performance
Official YouTube guidance checked 2026-09-28: since 2026-08-24, a public view is counted when playback begins across formats. YPP earnings continue to use engaged Shorts views and YPP eligibility uses qualified Shorts views. Therefore do not optimize or report Shorts success from raw public views alone. Primary learning set: engaged views, stayed-to-watch/chose-to-view behavior, average view duration/retention, subscribers and monetization metrics when available.
Sources:
- https://support.google.com/youtubecreatorstudio/answer/2991785
- https://support.google.com/youtubecreatorstudio/answer/12220281

### Official rule VP-005 — hook and packaging are promises; tags are secondary
Official YouTube recommendation guidance says initial seconds are a key stay/leave decision point, the intro should immediately deliver on the title/thumbnail promise, and retention should be used to evaluate structure. Titles/thumbnails/description matter for packaging; tags are mainly useful for spelling variants rather than being an essential discovery lever.
Source: https://support.google.com/youtube/answer/16559650

### Official rule VP-006 — no universal favored Shorts format
Official Shorts search/discovery guidance says YouTube does not inherently favor a particular Shorts format; ranking depends on performance and viewer personalization. Treat third-party creator advice, books, TikTok/Reels patterns, vidIQ findings and viral examples as discovery inputs/hypotheses, never as proof of a YouTube algorithm rule.
Source: https://support.google.com/youtube/answer/11914225

## Existing official production guardrails
- Technical upload encoding/QC source already cataloged: `src_527e9618377fed71`.
- YouTube automatic-caption/intelligibility source already cataloged: `src_dba1a72aa5f4fc73`.
- YouTube monetization/originality source already cataloged: `src_d9ad3569da502ff8`.

Production gate:
1. 9:16 playable MP4 exists.
2. Narration/audio is actually present and intelligible.
3. Captions match speech closely enough for review.
4. Visual/audio timing is synchronized.
5. Claims are fact-checked.
6. Originality/rights/monetization risk is acceptable.
7. One explicit learning hypothesis is attached to the upload.
8. After enough data, feed measured results back into this pool and supersede weak hypotheses rather than repeating them.

## Shared automation usage
- `Video ve Shopify Otomasyonu`: primary consumer and producer of video-production learnings. Must check this pool before topic/script/edit decisions and write new verified lessons after meaningful analysis.
- `Bilgi Kütüphanesi`: dedup/index owner. Promote stable lessons into machine source/learning ledgers when write + read-back validation is actually available.
- `Sistem Geliştirmeleri`: use this pool to improve production tooling, QC, analytics routing and low-cost research order; do not reinterpret creative observations as technical facts.
- `Finans`: only consume a production lesson when creating finance-related media/report visuals; never use video popularity as financial evidence.

## Evidence discipline
- Public view counts are snapshots and can change.
- One successful video does not prove a causal formula.
- Search-ranking/trending surfaces are discovery tools, not controlled experiments.
- The strongest production learning comes from combining external patterns with our own retention/engagement/monetization results.
- Copyrighted source material is for analysis only; do not copy scripts, footage or distinctive creative expression.
