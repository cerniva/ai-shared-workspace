# YouTube Shorts publisher

The uploader in `scripts/youtube_upload.py` sends an already rendered MP4 to the Cerno channel (`UCAKg-ZKPoazTnF2zDVORk4Q`) using YouTube Data API `videos.insert`.

## One-time account setup

1. In Google Cloud, enable YouTube Data API v3 and configure an OAuth client.
2. Grant the uploader the `https://www.googleapis.com/auth/youtube.upload` OAuth scope while signed into the Google account that owns the target channel.
3. Keep the OAuth client secret and refresh token in a private secret manager. Never put them in this public repository, a workflow input, or chat.
4. If the API project is subject to YouTube's unverified-project restriction, complete Google's API audit before expecting public visibility.

The current Codex task runner does not have this write-scoped refresh token or a secure persistent secret handoff. A signed-in Studio browser session and vidIQ identity verification do not replace this OAuth grant.

## Run

Install dependencies from `scripts/requirements-youtube.txt`. Set these environment variables using a private secret manager:

- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN` (must have the upload scope)

Create a UTF-8 JSON metadata file:

```json
{
  "title": "Your original Shorts title",
  "description": "Description and source credits"
}
```

Then run:

```sh
python3 scripts/youtube_upload.py finished.mp4 metadata.json --publish
```

Without `--publish`, the script uploads privately. Before uploading, it confirms the OAuth identity owns the configured channel. After upload, it checks the returned video ID, channel, and visibility, and prints a URL only after those checks pass.

## Remaining automation handoff

This command is a publisher component, not a complete scheduled pipeline. The daily video producer must call it in an environment that has the OAuth secrets and the rendered MP4. The current ChatGPT task workspace cannot pass its scratch MP4 or the user's phone browser session to GitHub Actions. Do not claim automated publication until that handoff and a successful public upload have both been verified.
