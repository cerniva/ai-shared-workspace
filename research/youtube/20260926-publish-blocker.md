# YouTube Shorts publication blocker — 2026-09-26

## Verified

- The connected vidIQ account recognizes the user's YouTube channel, so channel discovery is working.
- The current vidIQ YouTube authorization check returns `verification_required`.
- Available vidIQ tools can inspect the connected channel and host/import MP4 assets, but the available tool catalog has no YouTube video-create/upload operation. `vidiq_video_upload` hosts an asset; it does not publish it to YouTube.
- The public workspace's `youtube_client.py` uses `YOUTUBE_API_KEY` for read operations. `youtube_analytics_client.py` requests channel analytics with the readonly OAuth setup. There is no `videos.insert` implementation or publishing workflow.
- Chrome's YouTube session is signed out. YouTube Studio redirects to Google sign-in.

## Root cause

A connected YouTube channel and read-only analytics authorization were mistaken for an active publishing capability. The previous two uploads may have used a different session or workflow; no publishing audit trail for them exists in this workspace, so their route cannot be asserted.

## Durable correction

- The user's 2026-09-26 standing instruction authorizes routine daily Shorts publication to the connected YouTube channel without routine approval.
- That instruction is recorded in `PROTOCOL.md`.
- Do not mark a Short as published based on MP4 rendering or vidIQ asset hosting. Confirm a YouTube video ID or Studio publication result.
- When using the YouTube Data API, a publishing flow requires OAuth `youtube.upload` authorization and `videos.insert`. Readonly API keys/tokens cannot upload. Newer unverified API projects may restrict API uploads to private visibility until the project passes YouTube's audit.

## Current deliverable

`shorts_bugun.mp4` exists in the workspace and is not confirmed as published. Google account sign-in is required in the available YouTube Studio browser session before UI-based upload can continue.
