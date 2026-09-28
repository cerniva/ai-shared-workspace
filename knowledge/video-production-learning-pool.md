# Video Production Learning Pool

Status: active shared knowledge
Updated: 2026-09-29
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

### Operational rule VP-007 — Metricool publish state is fail-closed
For the verified Metricool YouTube fallback, a production-ready scheduled Short must have `providers=[youtube]`, `youtubeData.type=short`, a real video media object/URL, required title and audience declaration, `draft=false`, and `autoPublish=true`. A record with `draft=true` or `autoPublish=false` is not an automated YouTube publication and must never be reported as published. Metricool `Pending` means scheduled/waiting, not published. After the due time, require remote planner/network evidence before reporting success.
Source: https://help.metricool.com/wli-scheduler-endpoint-example-on-a-custom-backend-proxy-frko7

### Operational rule VP-008 — scheduling time guard and duplicate protection
Before creating/updating a scheduled publication, compare the requested Europe/Istanbul time with current time and require a future timestamp plus a small safety margin. A past timestamp can return HTTP 400. On 400, fix schema/input/time rather than retrying unchanged. On timeout/uncertain response, query Metricool/YouTube for the same UUID/media/title before creating another upload. Never use two upload paths for the same daily Short.
Source: https://help.metricool.com/wli-scheduler-endpoint-example-on-a-custom-backend-proxy-frko7

### Operational rule VP-009 — publication success is an end-to-end state machine
Do not collapse render, scheduling and publication into one success flag. Required states are: `MP4_EXISTS -> QA_PASS -> REMOTE_SCHEDULED -> REMOTE_PUBLISHED -> ANALYTICS_READY`. QA_PASS requires playable 9:16 MP4, H.264 video, AAC audio with a real non-silent signal, captions, A/V sync, complete decode, factual/originality/rights checks. A Metricool-accepted media URL does not prove audio or decode quality. Direct YouTube OAuth `invalid_grant` is not retried blindly; use the already-authorized Metricool fallback until OAuth is interactively repaired. Any failure remains explicit and cannot be promoted to DONE by a later unrelated step.

## Shorts production framework — 2026-09-29

### Rule VP-010 — 30-second standard
Default production duration for every planned Short is exactly 30 seconds. Design hook, development, payoff and loop/CTA for this duration rather than stretching a weak idea. A platform capability to host longer Shorts is not a reason to lengthen production.

### Rule VP-011 — 200-idea research pool is a production source
Before choosing a topic, use the researched 200-format idea pool as a discovery/benchmark source. It spans satisfying food/bento, cleaning/detailing, transformations/restoration, crafts, experiments, quizzes/games, comparison/ranking, sports, gaming, travel, science/nature, collectibles, music/audio, storytelling, animation/AI and other tested demand families. Do not force a category merely because it is in the pool: re-check current public evidence and choose the strongest viable candidate.

### Rule VP-012 — 40 retention/engagement mechanisms are production rules
Score candidate Shorts against the researched retention mechanisms and deliberately combine the most relevant 3–5 rather than inserting all of them. Mechanism set includes: transformation; satisfying/ASMR; curiosity gap; payoff/reveal; prediction/game; comparison; surprise/novelty; skill admiration; story/tension; community/debate; open loop; pattern interrupt; progress indicator; escalating difficulty; risk/failure possibility; twist; hidden detail; withheld information; micro-payoffs; countdown; forced choice; self-test; myth correction; expectation reversal; scale surprise; rarity; inaccessible-world access; visible craft skill; error-to-fix; problem-to-solution; before/after; anticipated impact moment; seamless loop; comment disagreement; identity/community signal; nostalgia; relatability; series/progression; viewer-directed next choice; sensory sound reward.

### Rule VP-013 — candidate selection order
For each production cycle: current demand/performance evidence -> fit to 30 seconds -> hook strength -> choose 3–5 retention mechanisms -> production feasibility/cost -> rights/originality/monetization gate -> script/visual/audio plan -> QA -> publish -> analytics learning. Public search snippets are discovery only; critical claims should be checked against primary/official sources when possible.

### Rule VP-014 — satisfying food and transformation are priority lanes, not mandatory topics
Satisfying food/bento/meal-prep and satisfying cleaning/detailing/transformation are validated priority lanes. Favor immediate visual payoff, fast 1–2 second process shots when appropriate, strong before/after contrast, natural sensory sound/ASMR when useful, curiosity, reveal and loop-friendly endings. Do not lock the channel to food or cleaning when another researched format has stronger current evidence.

### Rule VP-015 — viral examples are benchmarks, not copy masters
Prioritize unusually successful/high-view examples for analysis of hook, pacing, scene order, curiosity, audio, captions, payoff, loop and audience reaction. If direct reuse rights are explicitly verified, material may be used only within those license/permission terms. Otherwise copyrighted footage/audio/scripts/distinctive expression are analysis-only: create original visuals, audio, narration and script. Never treat “many people repost it”, absence of a visible claim, or changing a few seconds as copyright or monetization clearance.

### Rule VP-016 — money + engagement optimization is constrained by rights
Optimization objective is not raw views alone. Optimize for engaged/qualified performance, retention, rewatch, likes/comments/shares, subscriber impact and monetization eligibility while keeping copyright, reused-content and inauthentic/mass-produced-content risk acceptable. Rights/originality gate overrides a high predicted view count.

### Rule VP-017 — 30-second structural baseline
Default test structure: 0–2 s scroll-stopper/hook; 2–6 s curiosity/problem/prediction; 6–20 s rapid progress with useful micro-payoffs; 20–27 s main payoff/reveal; 27–30 s natural loop, concise CTA or comment choice only when it improves the concept. This is a hypothesis/template, not an algorithm law; supersede it when owned-channel retention data supports a better structure.

### Rule VP-018 — learning loop
After publication, prefer engaged views, stayed-to-watch/chose-to-view, first-seconds retention when available, average view duration, average percentage viewed, rewatch/loop evidence, likes, comments, shares, subscribers and monetization metrics. Record which topic family and retention mechanisms were used. Promote patterns only after repeated owned-channel evidence; do not infer causality from one viral external example.

## Existing official production guardrails
- Technical upload encoding/QC source already cataloged: `src_527e9618377fed71`.
- YouTube automatic-caption/intelligibility source already cataloged: `src_dba1a72aa5f4fc73`.
- YouTube monetization/originality source already cataloged: `src_d9ad3569da502ff8`.

Production gate:
1. 9:16 playable MP4 exists.
2. Duration is 30 seconds under the current production standard.
3. Narration/audio is actually present and intelligible.
4. Captions match speech closely enough for review.
5. Visual/audio timing is synchronized.
6. Claims are fact-checked.
7. Originality/rights/monetization risk is acceptable.
8. Candidate was evaluated against the 200-idea pool and relevant retention mechanisms.
9. One explicit learning hypothesis is attached to the upload.
10. After enough data, feed measured results back into this pool and supersede weak hypotheses rather than repeating them.

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
