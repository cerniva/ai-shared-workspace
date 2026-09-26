# YouTube Shorts publishing gap — 2026-09-26

## Current verified state

- Connected vidIQ channel: `UCAKg-ZKPoazTnF2zDVORk4Q`.
- The vidIQ YouTube identity check returned `verified` on 2026-09-26. The channel is connected. vidIQ balance is 0; that blocks paid research tools, not a YouTube upload endpoint.
- The user supplied a screenshot at 18:15 showing YouTube Studio signed in to the Cerno channel in Chrome on their iPhone. This proves the user's phone session is authenticated. The separately controlled Chrome session available to this workspace still shows Google's sign-in page; the phone's session is not shared with it.
- The available vidIQ tool `video_upload` imports and hosts an MP4. It does not publish to YouTube. The current tool catalog has no YouTube `videos.insert` / publish action.
- The GitHub repository has no YouTube upload script or publication workflow in `.github/workflows`.
- The previous Google OAuth setup requested readonly scopes (`youtube.readonly` and `yt-analytics.readonly`). These cannot upload. An API key also cannot publish videos.
- The daily MP4 `shorts_bugun.mp4` exists in the task workspace; there is no confirmed YouTube video ID or published URL.

## Root cause

Authentication to Studio and identity verification through vidIQ were mistaken for a programmatic publishing capability. The user's Chrome session is not accessible from the controlled Chrome session, and no publisher is implemented in the connected tools or repository.

## Requirements for real daily auto-publishing

1. An OAuth refresh token granted the `https://www.googleapis.com/auth/youtube.upload` scope, stored in a private secret manager (never in chat or a public repo).
2. A verified YouTube API project. Google restricts uploads from unverified API projects created after 2020-07-28 to private visibility until the project passes its audit.
3. A secure way for each generated MP4 and its metadata to reach the uploader, plus a trigger that the daily content job can invoke. Current task files live in scratch storage; the GitHub connector cannot dispatch a workflow or upload binary artifacts to it.
4. An uploader that calls YouTube Data API `videos.insert`, checks the returned video ID/visibility, and reports success only after verification.

## Authorization and current result

- The user's standing instruction authorizes routine Shorts publication to the connected channel without routine approval; it is recorded in `PROTOCOL.md`.
- No video was published in this run. Do not report publication based on Studio login, MP4 rendering, or vidIQ hosting alone.
- This workspace can continue research and render daily MP4s, but unattended YouTube publication is not configured until the OAuth write scope, project audit status, secure asset handoff, and trigger path are resolved.
