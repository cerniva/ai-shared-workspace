# YouTube Shorts publishing status — 2026-09-26

## Verified state

- Channel: `UCAKg-ZKPoazTnF2zDVORk4Q`; vidIQ identity verification returned `verified`. vidIQ balance is 0; that affects paid research only.
- User's iPhone Chrome screenshot at 18:15 showed YouTube Studio already signed into Cerno. Do not ask the user to sign in again. This runner's separate browser does not inherit the phone's session.
- vidIQ `video_upload` imports/hosts MP4s; it does not publish to YouTube. The connected tool catalog has no YouTube publishing operation.
- Added `scripts/youtube_upload.py` with resumable `videos.insert`, fixed target-channel validation, and post-upload ID/channel/privacy verification. Added dependency list and OAuth runbook. Local credentials are git-ignored.
- The daily MP4 exists in task scratch storage; it has not been published and has no confirmed YouTube video ID.

## Remaining blockers

1. No refresh token with `https://www.googleapis.com/auth/youtube.upload` is available to the runner. Previous Google OAuth setup used read-only scopes. Studio login or an API key cannot replace user OAuth upload permission.
2. No secure persistent way currently passes the task's scratch MP4 and metadata to an environment where the uploader and OAuth secrets can run. No GitHub workflow can access this scratch path.
3. Audit status for the Google API project has not been verified. Google restricts public visibility from unverified projects created after 2020-07-28.

## Result and next implementation step

- The user authorized routine publication without routine approval. That authorization is recorded in `PROTOCOL.md`.
- No video was published. Never report success based on Studio login, local rendering, or vidIQ hosting.
- Publisher code is ready, but daily auto-publication is not. The account owner must grant the OAuth upload scope once through a secure consent flow and store the refresh token in a private secret manager. The content producer must then hand the rendered MP4 to the same runner. Once those are available, invoke the script and verify the resulting video ID/channel/visibility.
