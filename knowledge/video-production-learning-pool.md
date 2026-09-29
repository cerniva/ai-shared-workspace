# Video Production Learning Pool

Status: active shared knowledge
Updated: 2026-09-29
Scope: YouTube Shorts and reusable production lessons for scripting, editing, visuals, audio, packaging, publishing and analytics.

## Purpose
Shared production knowledge for Video/Shopify, Bilgi Kütüphanesi and Sistem Geliştirmeleri. Dedup before research. PayoutLens is out of scope.

## Research order — cost first
1. Existing shared state/catalog and this pool.
2. Public discovery/trend sources and cheap metadata.
3. Transcripts/comments/community patterns.
4. Owned-channel analytics.
5. Expensive scene analysis/generation only for finalists.

## Topic reuse and visual originality — mandatory
- A successful or similar topic/content family may be revisited when current demand, owned analytics or a new test hypothesis justifies it.
- A new Short must not reuse the same footage, shot sequence, or visual asset set from the previous Short as its production basis. Use newly sourced/created rights-safe visuals or genuinely new footage.
- Topic reuse does not make a derivative re-edit acceptable: require a new hook/angle or viewer value, a new edit/scene plan, and a new testable hypothesis.
- Record prior-video similarity and the new visual provenance so duplicate-footage checks can fail closed before publish.
- Rights/license/originality/monetization checks still apply to every new asset. Cropping, mirroring, trimming, recoloring, speed changes or a few replacement shots do not turn reused footage into a new original Short.

## Expanded discovery + production source stack
Trend/idea discovery: Google/TinyFish, YouTube, vidIQ, Metricool, TikTok Creative Center, Instagram Reels, Google Trends, Reddit, Pinterest Trends, Exploding Topics, AnswerThePublic, Google Keyword Planner, Wikipedia Pageviews, GDELT, Product Hunt, GitHub Trending/public GitHub, SteamDB/public game data, YouTube Comments.
Primary factual/media: Google Arts & Culture, NASA, NOAA and other official/first-party sources.
Rights-aware assets: Wikimedia Commons, Internet Archive, Pexels, Pixabay, Mixkit, Freesound, YouTube Audio Library/supported Shorts audio. Verify item-level rights.
Original production: Runway, Higgsfield, OpenArt, Canva, Remotion/programmatic video, Blender and legitimate TTS/voice tools.

## AUDIO SOURCE + TOOL CATALOG — 2026-09-29
Purpose: eliminate silent/weak-audio Shorts while improving narration, ASMR/SFX, music, mixing and automated QC. `access_status` is conservative: a source mentioned/researched is not treated as connected until verified. Never spend paid credits merely to test a candidate when a free/local route can answer the same need.

### A. Music / SFX / ambience / Foley sources
1. YouTube Audio Library — music + SFX; preferred YouTube-native rights-safe source; some tracks require attribution. Status: web/platform available; account workflow may require Studio access.
2. YouTube supported Shorts audio — platform-native Short audio where intended use is covered. Status: platform available; use conditions must be checked.
3. Freesound — SFX/ambience/foley under item-specific CC licenses. Status: web available; commercial use/attribution varies per item.
4. Mixkit — stock music/SFX. Status: web available; verify current item/license terms.
5. Pixabay Audio — music/SFX. Status: web available; verify current license/restrictions.
6. Uppbeat — music/SFX catalog. Status: available_unverified for current account/quota; free tier is limited; verify licensing before monetized use.
7. BBC Sound Effects Archive — large sound-effect archive. Status: web discovery; usage/license must be checked for each intended commercial use.
8. ZapSplat — SFX/foley/ambience. Status: web discovery; account/license/attribution rules must be checked.
9. Sonniss GDC bundles — professional SFX bundles. Status: web discovery; verify bundle-specific license.
10. Openverse Audio — Creative Commons/public-domain audio discovery layer. Status: web discovery; verify original source/license.
11. Free Music Archive — music discovery. Status: web discovery; item-level license required.
12. Incompetech — music source. Status: web discovery; verify attribution/license for selected track.
13. Bensound — music source. Status: web discovery; free/commercial conditions vary; verify selected license.
14. Original recorded Foley — self-created crunch/sizzle/click/scrape/cut/pour/room tone. Status: preferred original route when feasible; record provenance.
15. Original generated SFX/music — use only a generator whose output/commercial terms are verified. Status: tool-dependent.

### B. Narration / TTS / voice sources
16. eSpeak NG — local/offline zero-credit TTS; currently supported by `scripts/shorts_render.py`. Status: verified in code; quality fallback rather than preferred natural voice.
17. Piper TTS — local/offline TTS candidate. Status: candidate/unverified in production environment.
18. Kokoro TTS — open-weight/local TTS candidate with offline-capable implementations. Status: researched candidate; environment/voice/language quality must be tested before production default.
19. ElevenLabs — natural TTS/SFX-capable service. Status: available_unverified; quota/cost/rights must be checked before use.
20. Fish Audio — TTS/voice candidate. Status: available_unverified; verify plan, rights and access.
21. Google Cloud Text-to-Speech — multilingual TTS candidate. Status: available_unverified; API/billing/quota required before use.
22. Microsoft Azure AI Speech — neural multilingual TTS candidate. Status: available_unverified; API/billing/quota required before use.
23. Coqui XTTS — local/customizable TTS research candidate. Status: unverified; check current project/license/model terms before use.
24. MeloTTS — local/open-source TTS candidate. Status: unverified; test language quality/license before use.
25. Legitimate connected TTS/voice tools — generic fallback category only; never clone a real person's voice without authorization and never treat availability as verified without a successful call.

### C. Cleaning / mixing / mastering / editing
26. FFmpeg — deterministic mix, AAC encode, filters, loudness/silence analysis. Status: core production dependency in repo.
27. Adobe Podcast Enhance Speech — speech cleanup/enhancement candidate. Status: web/app capability candidate; verify access/limits before automation.
28. Audacity — local editing, noise reduction, EQ/compression/limiting. Status: local software candidate.
29. DaVinci Resolve Fairlight — professional mix, ducking, EQ, limiter/loudness. Status: desktop candidate; not assumed installed.
30. Adobe Audition — professional audio cleanup/mix. Status: app candidate; access not assumed.
31. REAPER — DAW/mixing candidate. Status: desktop candidate; license/install not assumed.
32. DeepFilterNet — local AI speech/noise cleanup candidate. Status: unverified in environment.
33. RNNoise — lightweight local noise suppression candidate. Status: unverified in environment.
34. Rubber Band — time-stretch/pitch tool for fitting narration without crude truncation. Status: unverified in environment.
35. SoX — command-line audio conversion/processing/QC candidate. Status: unverified in environment.
36. Demucs — stem/voice/music separation for legitimate source material. Status: unverified; do not use to evade copyright restrictions.

### D. Automated QC / speech / signal analysis
37. `scripts/shorts_preflight.py` — repository fail-closed technical gate: H.264, 9:16, AAC, full decode, audio signal plus independent review. Status: verified repo capability.
38. FFmpeg `volumedetect` — current audio-signal measurement used by preflight. Status: implemented.
39. FFmpeg `silencedetect` — candidate for long/unwanted silence detection. Status: planned enhancement, not yet claimed implemented.
40. FFmpeg `loudnorm` / EBU R128 — candidate for loudness normalization. Status: FFmpeg capability; production integration not yet verified.
41. FFmpeg `ebur128` — candidate loudness measurement/QC. Status: capability; integration unverified.
42. Whisper — speech transcription/intelligibility/caption verification candidate. Status: candidate; local model/runtime not assumed available.
43. Silero VAD — speech-region detection candidate. Status: unverified in environment.
44. WebRTC VAD — speech/silence-region detection candidate. Status: unverified in environment.
45. librosa — programmatic energy/beat/audio analysis candidate. Status: unverified in production environment.
46. Essentia — programmatic loudness/rhythm/spectral analysis candidate. Status: unverified in environment.
47. AudioSet — sound-event taxonomy/reference for classifying/describing SFX; not itself a rights-free production asset library. Status: research/reference.

### E. Generative audio / music research candidates
48. AudioCraft / MusicGen — original music generation research candidate. Status: unverified; model/license/commercial-use terms must be checked before monetized production.
49. Stable Audio Open — generative audio/SFX research candidate. Status: unverified; model/output license and runtime requirements must be checked.

### Audio routing and selection rules
- Narration priority: verified natural free/local TTS -> legitimate quota-free/low-cost connected TTS -> eSpeak NG fallback. Never silently spend paid credits.
- Satisfying/food priority: original Foley/ASMR first; then rights-verified SFX. Mechanism #2 Satisfying/ASMR and #40 sensory sound reward should influence sound design when selected.
- Music priority: YouTube Audio Library / rights-verified original or licensed music. Music is optional; do not mask narration/ASMR just to fill silence.
- External asset rule: store source/provenance/license/attribution requirement for each external audio asset. 'Free', 'royalty-free' or being widely reposted is not sufficient proof.
- Commercial filter: reject non-commercial licenses for monetized Shorts unless separate commercial permission is verified.
- Cost rule: free/local first; paid API/generation only for a finalist when it materially improves expected quality and is authorized.

### Mandatory audio production gate
A Short must not reach upload/publish unless all applicable checks pass for the exact MP4 bytes:
1. Audio stream exists and is AAC in final MP4.
2. Full file decodes without media errors.
3. Real audio signal exists; a silent track is a failure.
4. Speech, when used, is intelligible by independent review; future automated transcription/VAD can supplement but not fabricate this evidence.
5. A/V sync passes independent review.
6. Music does not overpower narration or key ASMR/Foley.
7. External audio provenance/license is recorded and monetized use is allowed.
8. Preflight `ready=true` and SHA-256 matches the exact file sent to upload.
9. Upload path must fail closed if preflight evidence is missing/mismatched.
10. After publication, remote playback/audio should be checked when a supported authorized path exists; scheduling/HTTP success alone is not proof that viewers hear audio.

## EDITING TECHNIQUE CATALOG — 2026-09-29
Purpose: choose edits because they serve attention, comprehension, pacing, payoff or continuity—not because an effect exists. YouTube's official Shorts editor supports clip trim/reorder, precise timeline editing, timed text, voiceover, volume control and beat-sync; these capabilities validate the production primitives, but they do not prove that any named editing technique causes higher retention. Treat the technique-to-performance link as a testable hypothesis and learn from owned analytics.

### Core cuts and continuity
1. Jump cut — remove dead time/repetition while preserving meaning.
2. Hard cut — direct scene change with no decorative transition.
3. Action cut / cut on action — change shot during motion to preserve momentum.
4. Match cut — connect similar shape, motion, framing or concept across scenes.
5. Smash cut — abrupt contrast for surprise/comedy/intensity.
6. J-cut — next scene's audio starts before its picture.
7. L-cut — previous scene's audio continues under the next picture.
8. Sound bridge — use continuous/anticipatory sound to connect scenes.
9. POV continuity — preserve viewer orientation/perspective across cuts.
10. Eyeline/direction continuity — preserve movement and gaze direction unless deliberate disorientation is the point.

### Pace and compression
11. Progress montage — compress a longer process into visible milestones.
12. Montage compression — condense many informational steps into a short sequence.
13. Speed ramp — accelerate low-value motion and/or slow the decisive moment when clarity benefits.
14. Timelapse / hyperlapse — compress long transformations or travel/process time.
15. Freeze frame — pause on a critical detail/question/error.
16. Frame hold + zoom — hold and magnify a detail the viewer may miss.
17. Reverse — reverse motion only when it adds clarity, surprise or loop value.
18. Looped action — repeat a satisfying/important motion sparingly.
19. Beat cut — align selected edits with musical rhythm when music serves the concept.
20. Sound-hit cut — align an edit/reveal with a legitimate impact/Foley cue.

### Attention and visual reset
21. Punch-in / digital zoom — emphasize a detail, reaction or key phrase.
22. Macro reveal — withhold then reveal close detail/texture.
23. Pattern interrupt — deliberately break an established visual/audio rhythm.
24. Visual reset — materially change framing, scale, angle, background or information state.
25. Split screen — show simultaneous comparison/progress.
26. Side-by-side A/B — make before/after, cheap/expensive, correct/wrong or other contrast legible.
27. Picture-in-picture — keep reaction/explanation/context visible over primary footage.
28. Foreground wipe — hide a cut behind a passing object when continuity benefits.
29. Mask transition — use an object/shape as a motivated transition.
30. Whip transition — use rapid directional motion to bridge shots; avoid when it reduces comprehension.
31. Rack-focus transition — use focus change to shift attention/bridge scenes when footage supports it.

### Curiosity, narrative and payoff
32. Flash-forward — show a small fragment of the result early without exhausting the payoff.
33. Open-loop editing — introduce a question/promise that later shots genuinely resolve.
34. Delayed reveal — postpone the full answer/result while delivering enough progress to avoid baiting.
35. Micro-payoff — deliver intermediate rewards before the main payoff.
36. Escalation edit — make successive beats meaningfully stronger/harder/larger/more consequential.
37. Expectation reversal — reveal a legitimate outcome that contradicts the viewer's reasonable prediction.
38. False ending — briefly signal completion before a genuine extra beat; use sparingly, never deceptive padding.
39. Callback — return to an earlier object/question/line to create closure.
40. Seamless loop — make the ending naturally connect to the opening when replay adds value.

### Text and information editing
41. Text reveal — stage information instead of dumping it all at once.
42. Kinetic typography — animate text only when motion reinforces meaning/timing.
43. Caption emphasis — selectively emphasize critical words; preserve readability.
44. Object-tracked text — anchor labels/context to a moving subject when it improves understanding.
45. Timed captions/text — synchronize text appearance/disappearance to the relevant spoken or visual beat.
46. Minimal-text mode — omit nonessential text when visual action and sound already communicate clearly.

### Audio-led editing
47. Silence drop — deliberately reduce/cut audio immediately before an important sound/reveal when contrast helps.
48. Audio ducking — lower music/background under narration, Foley or key sensory sound.
49. Foley-sync edit — align cut/action with the actual or rights-safe recreated sound event.
50. Voiceover-led B-roll — let narration carry continuity while visuals change to evidence/context.

### Editing selection rule
- Do not apply all techniques. For each Short, evaluate the catalog and select only techniques with a defined job.
- Record selected techniques and intended job: `technique -> attention/comprehension/pacing/payoff/continuity`.
- Content-family routing examples: satisfying/food favors action cuts, macro reveal, progress montage, Foley-sync, micro-payoffs, silence drop and loop; transformation/restoration favors before/after comparison, progress montage, match/action cuts and escalation; quiz/factual favors question/open-loop, timed text, progressive clues, pattern interrupt, delayed reveal and callback; gaming/high-action favors action cuts, POV continuity, selective punch-ins, sound-hit cuts and readable captions.
- Never use random high-frequency cuts, zooms or transitions merely to simulate retention. Every cut should remove low-value time, introduce new information, redirect attention, preserve continuity or strengthen a promised payoff.
- Default 30-second structural hypothesis remains 0–2 s hook; 2–6 s curiosity/problem/prediction; 6–20 s progress + micro-payoffs; 20–27 s main payoff; 27–30 s loop/useful CTA. Override only when the concept or owned analytics supports a better structure.

### Editing QA gate
Before publish, verify: no accidental black/frozen frames; no unintended duplicate frames/scenes; captions/text remain inside safe readable areas and are synchronized; transitions do not obscure critical information; pacing has no unexplained dead segment; final payoff fulfills the opening promise; loop is natural if used; A/V sync and audio QA pass; exact MP4 passes the existing technical preflight. Editing style is then evaluated post-publication with owned Shorts analytics rather than assumed successful.

## Shorts production framework
- Default planned Short: exactly 30 seconds, 9:16.
- Evaluate the researched 200-format idea pool before choosing a topic.
- Evaluate all 40 retention/engagement mechanisms and combine the most relevant 3–5.
- Evaluate all 50 editing techniques and select only the techniques that serve a defined role; record the selected set.
- Candidate order: current demand/performance -> 30-second fit -> hook -> mechanisms -> editing plan -> feasibility/cost -> rights/originality/monetization -> script/visual/audio -> QA -> publish -> analytics.
- Satisfying food/bento/meal-prep and cleaning/detailing/transformation are priority lanes, not mandatory topics.
- Viral examples are benchmarks, not copy masters.
- Topic families may repeat when justified, but the new Short must use a fresh visual set/footage and deliver a new angle/value/hypothesis; same-footage re-edits fail the originality gate.
- Default structure hypothesis: 0–2 s hook; 2–6 s curiosity/problem/prediction; 6–20 s progress + micro-payoffs; 20–27 s payoff; 27–30 s loop or useful CTA/comment choice.

## Shared automation usage
Video/Shopify must consult this pool before production. Bilgi Kütüphanesi owns canonical dedup/index. Sistem Geliştirmeleri improves tooling/QC. Finans may consume production lessons only for finance media; popularity is never financial evidence.

## Evidence discipline
Public virality does not prove causality. Trend/community sources are discovery signals. Rights must be verified per asset. Strongest learning combines external patterns with owned-channel analytics.