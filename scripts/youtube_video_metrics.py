#!/usr/bin/env python3
"""Read-only YouTube Analytics API v2 metrics for one video or the whole channel.

Uses the existing Actions secrets YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET /
YOUTUBE_REFRESH_TOKEN. Never uploads, edits or publishes. The refresh token must
carry the ``yt-analytics.readonly`` scope; a token minted only with
``youtube.upload`` returns a structured ``insufficient_scope`` blocker instead
of data (exit 3).

Swipe-away ("stayed to watch" / "viewed vs swiped away") is a Studio-only
Shorts metric and is NOT exposed by the Analytics API; it is reported as null
here and is collected by the TinyFish Studio read (tinyfish_youtube.py).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from typing import Any, Callable, Mapping

TOKEN_URI = "https://oauth2.googleapis.com/token"
ANALYTICS_SCOPE = "https://www.googleapis.com/auth/yt-analytics.readonly"
METRICS = ("views", "engagedViews", "estimatedMinutesWatched", "averageViewDuration",
           "averageViewPercentage", "likes", "comments", "shares", "subscribersGained")
SECRETS = ("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET", "YOUTUBE_REFRESH_TOKEN")


def build_query(video_id: str | None, start: dt.date, end: dt.date) -> dict[str, Any]:
    q: dict[str, Any] = {"ids": "channel==MINE", "startDate": start.isoformat(),
                         "endDate": end.isoformat(), "metrics": ",".join(METRICS)}
    if video_id:
        q["filters"] = f"video=={video_id}"
    return q


def parse_report(resp: Mapping[str, Any]) -> dict[str, Any]:
    headers = [h.get("name") for h in resp.get("columnHeaders", [])]
    rows = resp.get("rows") or []
    values = dict(zip(headers, rows[0])) if rows else {}
    out: dict[str, Any] = {name: values.get(name) for name in METRICS}
    minutes = out.get("estimatedMinutesWatched")
    out["watch_time_hours"] = round(minutes / 60, 3) if isinstance(minutes, (int, float)) else None
    views, likes = out.get("views"), out.get("likes")
    out["likes_per_1k_views"] = round(likes / views * 1000, 2) if views and isinstance(likes, (int, float)) else None
    engaged = out.get("engagedViews")
    # engaged/views is an API-side proxy only; it is not Studio's "stayed to watch".
    out["engaged_ratio"] = round(engaged / views, 4) if views and isinstance(engaged, (int, float)) else None
    out["stayed_to_watch_percent"] = None
    out["has_data"] = bool(rows)
    return out


def _default_client(env: Mapping[str, str]):  # pragma: no cover - network
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(token=None, refresh_token=env["YOUTUBE_REFRESH_TOKEN"], token_uri=TOKEN_URI,
                        client_id=env["YOUTUBE_CLIENT_ID"], client_secret=env["YOUTUBE_CLIENT_SECRET"])
    return build("youtubeAnalytics", "v2", credentials=creds, cache_discovery=False)


def fetch(video_id: str | None, start: dt.date, end: dt.date, env: Mapping[str, str] | None = None,
          client_factory: Callable[[Mapping[str, str]], Any] = _default_client) -> dict[str, Any]:
    env = os.environ if env is None else env
    missing = [s for s in SECRETS if not str(env.get(s, "")).strip()]
    base = {"video_id": video_id, "start": start.isoformat(), "end": end.isoformat(), "source": "youtube_analytics_api_v2"}
    if missing:
        return {**base, "status": "blocked", "reason_code": "missing-secret", "missing": missing}
    try:
        client = client_factory(env)
        resp = client.reports().query(**build_query(video_id, start, end)).execute()
    except Exception as exc:  # googleapiclient HttpError / RefreshError
        text = str(exc)
        code = "insufficient_scope" if ("insufficient" in text.lower() or "403" in text or "scope" in text.lower()) else "api_error"
        if "invalid_grant" in text:
            code = "invalid_grant"
        return {**base, "status": "blocked", "reason_code": code, "detail": text[:400],
                "needs_scope": ANALYTICS_SCOPE if code == "insufficient_scope" else None}
    return {**base, "status": "COMPLETED", "metrics": parse_report(resp)}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--video-id")
    p.add_argument("--start", help="YYYY-MM-DD (default: 28 days ago)")
    p.add_argument("--end", help="YYYY-MM-DD (default: today)")
    a = p.parse_args(argv)
    end = dt.date.fromisoformat(a.end) if a.end else dt.date.today()
    start = dt.date.fromisoformat(a.start) if a.start else end - dt.timedelta(days=28)
    result = fetch(a.video_id, start, end)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "COMPLETED" else 3


if __name__ == "__main__":
    sys.exit(main())
