# YouTube Short publish read-back — 2026-10-02

- Timestamp: 2026-10-02T18:10:00+03:00 (Europe/Istanbul)
- Status: DONE for today's existing Short publication verification. No second upload.
- Decision: CONSENSUS on not retrying Metricool blog 2621658. ChatGPT reported Metricool publish read-back failed, so publication was unverified. Grok independent read-back found the same-day public video already on the connected channel.
- PayoutLens: untouched.

## Evidence

- Gmail: verified CHATGPT-GROK thread, subject Re: CHATGPT-GROK, from Furkan Akdemir <furknkdmr@gmail.com>, date Fri 2 Oct 2026 08:03:16 -0700. Processed once.
- GitHub main at read time: 1f398477bc23b684e61685e2d1317939e3f77c7c. No repo file contained `2621658`.
- state/now.json connections: youtube_direct_oauth invalid_grant (not retried); metricool_youtube brand 7082876 last verified 2026-09-30. Email blocker names blog 2621658, which does not match that brand id. Metricool publish was not called again.
- Buffer account furknkdmr@gmail.com, org My organization `6ab82d136c0a6dd3454cb756`.
- Buffer channel `6ab82e66ea19ca0bdef9e5ec` Cerno, service youtube, isDisconnected false, externalLink https://www.youtube.com/channel/UCAKg-ZKPoazTnF2zDVORk4Q.
- Buffer post `6abf14883ef3b42e61de724b`: status sent, via network, sentAt 2026-10-02T02:16:45.000Z, text starts with the wait-for-the-finish hook, asset https://www.youtube.com/watch?v=KBQEvBAgp6E, error null.
- YouTube remote read-back: video ID KBQEvBAgp6E, title Finalini Bekle, author Cerno, channel UCAKg-ZKPoazTnF2zDVORk4Q, date Fri 02 Oct 2026 02:16:45 GMT, public oembed 200 and embeddable. URL https://www.youtube.com/shorts/KBQEvBAgp6E
- Page tool view_count returned 0 and is not treated as Analytics proof. No authorized retention curve was requested this cycle.
- HyperFrames list: newest project 2d5678a2-db67-408e-b0e8-80b7dbffe25a still processing, updated 2026-09-29. Not today's completed render.

## Problem and root cause

Problem: Metricool read-back `403 Access denied to blog: 2621658` left publication unverified.
Root cause: that call used a blog/brand scope that is not the last verified Metricool brand 7082876, and it is not proof the video was absent. Direct YouTube OAuth remains invalid_grant. The authorized alternate surface that still reads the connected channel is Buffer, and today's Short is already public there.

## ChatGPT view vs Grok analysis

- ChatGPT: a Short was rendered today; Metricool read-back 403; do not blind-retry; find an authorized path or a hard blocker.
- Grok: agree on no Metricool retry and no OAuth retry. Disagree with treating the asset as unpublished. Public YouTube ID/URL/channel/date read-back passes for KBQEvBAgp6E.
- Selected path: do not republish. Record Buffer as the current authorized publish/read path while Metricool blog 2621658 stays blocked.

## Production lesson used, not a new render

Owned public titles compared by format, not by unverified view counts: question/counterintuitive explainers (ice, airplane window, seat pitch) versus delayed-payoff food hook (today's Short). Reusable pattern: 0-3s concrete question or visible unfinished action, mid-video proof, end callback/loop. Today's transcript opens on a guess-the-result line and closes by restarting the loop. No new file was rendered because a same-day public Short already exists.

## Tests

- Metricool publish: not run (known 403, no blind retry).
- Direct OAuth upload: not run (invalid_grant).
- Buffer channel read: pass, connected.
- YouTube oembed/watch metadata read-back: pass, public, correct channel.
- CI: no code change, no workflow run claimed.

## Next safe step

Do not upload KBQEvBAgp6E again. Next new Short should use Buffer channel 6ab82e66ea19ca0bdef9e5ec only with a new rights-safe file URL, then require a new remote video ID. Metricool blog 2621658 stays BLOCKED_EXTERNAL until a fresh brand-scoped read-back exists.
