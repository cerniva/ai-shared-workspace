#!/usr/bin/env python3
import json
import os
import re
import urllib.parse
import urllib.request

BASE = "https://www.googleapis.com/youtube/v3"
API_KEY = os.environ.get("YOUTUBE_API_KEY", "").strip()

class YouTubeDataError(RuntimeError):
    pass

def _get(path: str, params: dict) -> dict:
    if not API_KEY:
        raise YouTubeDataError("YOUTUBE_API_KEY secret eksik.")
    q = dict(params)
    q["key"] = API_KEY
    url = f"{BASE}/{path}?{urllib.parse.urlencode(q, doseq=True)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as exc:
        raise YouTubeDataError(f"YouTube Data API çağrısı başarısız: {exc}") from exc

def extract_video_id(url_or_id: str) -> str | None:
    value = (url_or_id or "").strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", value):
        return value
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", value)
    return m.group(1) if m else None

def video_details(url_or_id: str) -> dict:
    vid = extract_video_id(url_or_id)
    if not vid:
        raise YouTubeDataError("Geçerli YouTube video ID'si çıkarılamadı.")
    data = _get("videos", {
        "part": "snippet,contentDetails,statistics,status",
        "id": vid,
        "maxResults": 1,
    })
    items = data.get("items") or []
    return items[0] if items else {}

def channel_details(channel_id: str) -> dict:
    data = _get("channels", {
        "part": "snippet,statistics,contentDetails",
        "id": channel_id,
        "maxResults": 1,
    })
    items = data.get("items") or []
    return items[0] if items else {}

def search(query: str, max_results: int = 10, order: str = "relevance") -> list[dict]:
    data = _get("search", {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max(1, min(max_results, 25)),
        "order": order,
        "safeSearch": "moderate",
    })
    return data.get("items") or []

def comments(video_id: str, max_results: int = 20) -> list[dict]:
    data = _get("commentThreads", {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": max(1, min(max_results, 100)),
        "order": "relevance",
        "textFormat": "plainText",
    })
    return data.get("items") or []

def compact_video_bundle(url: str) -> dict:
    video = video_details(url)
    if not video:
        return {"url": url, "found": False}
    snippet = video.get("snippet") or {}
    stats = video.get("statistics") or {}
    channel_id = snippet.get("channelId")
    bundle = {
        "url": url,
        "found": True,
        "video": {
            "id": video.get("id"),
            "title": snippet.get("title"),
            "description": (snippet.get("description") or "")[:1800],
            "publishedAt": snippet.get("publishedAt"),
            "channelId": channel_id,
            "channelTitle": snippet.get("channelTitle"),
            "tags": (snippet.get("tags") or [])[:30],
            "categoryId": snippet.get("categoryId"),
            "duration": (video.get("contentDetails") or {}).get("duration"),
            "statistics": stats,
            "privacyStatus": (video.get("status") or {}).get("privacyStatus"),
        }
    }
    if channel_id:
        ch = channel_details(channel_id)
        cs = ch.get("snippet") or {}
        cstats = ch.get("statistics") or {}
        bundle["channel"] = {
            "id": channel_id,
            "title": cs.get("title"),
            "description": (cs.get("description") or "")[:1200],
            "publishedAt": cs.get("publishedAt"),
            "statistics": cstats,
        }
    try:
        bundle["topComments"] = comments(video.get("id"), 15)
    except YouTubeDataError as exc:
        bundle["commentsError"] = str(exc)
    return bundle
