#!/usr/bin/env python3
import datetime as dt
import json
import os
import urllib.parse
import urllib.request

CLIENT_ID = os.environ.get("YT_ANALYTICS_CLIENT_ID", "").strip()
CLIENT_SECRET = os.environ.get("YT_ANALYTICS_CLIENT_SECRET", "").strip()
REFRESH_TOKEN = os.environ.get("YT_ANALYTICS_REFRESH_TOKEN", "").strip()

class YouTubeAnalyticsError(RuntimeError):
    pass

def _access_token() -> str:
    if not CLIENT_ID or not CLIENT_SECRET or not REFRESH_TOKEN:
        raise YouTubeAnalyticsError(
            "YT_ANALYTICS_CLIENT_ID / YT_ANALYTICS_CLIENT_SECRET / YT_ANALYTICS_REFRESH_TOKEN eksik."
        )
    body = urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            data = json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        raise YouTubeAnalyticsError(f"OAuth access token alınamadı: {exc}") from exc
    token = data.get("access_token")
    if not token:
        raise YouTubeAnalyticsError(f"OAuth token yanıtı geçersiz: {data}")
    return token

def query_report(*, start_date: str, end_date: str, metrics: str,
                 dimensions: str | None = None, filters: str | None = None,
                 sort: str | None = None, max_results: int | None = None) -> dict:
    params = {
        "ids": "channel==MINE",
        "startDate": start_date,
        "endDate": end_date,
        "metrics": metrics,
    }
    if dimensions:
        params["dimensions"] = dimensions
    if filters:
        params["filters"] = filters
    if sort:
        params["sort"] = sort
    if max_results:
        params["maxResults"] = str(max_results)
    url = "https://youtubeanalytics.googleapis.com/v2/reports?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {_access_token()}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        raise YouTubeAnalyticsError(f"YouTube Analytics çağrısı başarısız: {exc}") from exc

def channel_overview(days: int = 28) -> dict:
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=max(1, days) - 1)
    return query_report(
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        metrics=(
            "views,estimatedMinutesWatched,averageViewDuration,likes,comments,"
            "subscribersGained,subscribersLost"
        ),
    )

def video_retention(video_id: str, days: int = 3650) -> dict:
    end = dt.date.today() - dt.timedelta(days=1)
    start = end - dt.timedelta(days=max(1, days))
    return query_report(
        start_date=start.isoformat(),
        end_date=end.isoformat(),
        dimensions="elapsedVideoTimeRatio",
        metrics="audienceWatchRatio,relativeRetentionPerformance",
        filters=f"video=={video_id}",
        sort="elapsedVideoTimeRatio",
        max_results=200,
    )
