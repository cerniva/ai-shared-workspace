#!/usr/bin/env python3
"""Upload a prepared Shorts MP4 to the configured YouTube channel.

Requires YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, and YOUTUBE_REFRESH_TOKEN.
The script never writes credentials to disk or prints token values.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

CHANNEL_ID = "UCAKg-ZKPoazTnF2zDVORk4Q"
UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def credentials_from_env():
    required = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    creds = Credentials(
        token=None,
        refresh_token=os.environ["YOUTUBE_REFRESH_TOKEN"],
        token_uri=TOKEN_URI,
        client_id=os.environ["YOUTUBE_CLIENT_ID"],
        client_secret=os.environ["YOUTUBE_CLIENT_SECRET"],
        scopes=[UPLOAD_SCOPE],
    )
    creds.refresh(Request())
    return creds


def load_metadata(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    title = data.get("title")
    description = data.get("description")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Metadata JSON must contain a non-empty 'title'.")
    if not isinstance(description, str):
        raise ValueError("Metadata JSON must contain a string 'description'.")
    return {"title": title.strip(), "description": description.strip()}


def upload(video: Path, metadata: dict, publish: bool) -> dict:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload

    creds = credentials_from_env()
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)

    channel_response = youtube.channels().list(part="id", mine=True).execute()
    channels = channel_response.get("items", [])
    if not any(item.get("id") == CHANNEL_ID for item in channels):
        ids = ", ".join(item.get("id", "<missing>") for item in channels) or "none"
        raise RuntimeError(f"Authorized account does not own target channel {CHANNEL_ID}; found: {ids}")

    status = {"privacyStatus": "public" if publish else "private"}
    body = {
        "snippet": {"title": metadata["title"], "description": metadata["description"]},
        "status": status,
    }
    media = MediaFileUpload(str(video), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    try:
        while response is None:
            progress, response = request.next_chunk()
            if progress is not None:
                print(f"Upload progress: {progress.progress() * 100:.0f}%", file=sys.stderr)
    except HttpError as exc:
        raise RuntimeError(f"YouTube upload failed (HTTP {exc.resp.status}). Check OAuth scope and API project status.") from exc

    video_id = response.get("id")
    if not video_id:
        raise RuntimeError("YouTube returned no video ID; upload cannot be verified.")

    verified = youtube.videos().list(part="snippet,status", id=video_id).execute().get("items", [])
    if not verified:
        raise RuntimeError(f"Upload {video_id} completed but could not be verified.")
    item = verified[0]
    if item.get("snippet", {}).get("channelId") != CHANNEL_ID:
        raise RuntimeError(f"Uploaded video {video_id} is not on the configured target channel.")
    expected_status = "public" if publish else "private"
    actual_status = item.get("status", {}).get("privacyStatus")
    if actual_status != expected_status:
        raise RuntimeError(f"Video {video_id} has visibility '{actual_status}', expected '{expected_status}'.")
    return {"video_id": video_id, "url": f"https://www.youtube.com/watch?v={video_id}", "privacy_status": actual_status}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path, help="Path to a finished MP4")
    parser.add_argument("metadata", type=Path, help="JSON file containing title and description")
    parser.add_argument("--publish", action="store_true", help="Publish publicly; default uploads privately")
    args = parser.parse_args()

    if not args.video.is_file() or args.video.suffix.lower() != ".mp4":
        parser.error("video must be an existing .mp4 file")
    if not args.metadata.is_file():
        parser.error("metadata JSON file does not exist")

    try:
        result = upload(args.video, load_metadata(args.metadata), args.publish)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
