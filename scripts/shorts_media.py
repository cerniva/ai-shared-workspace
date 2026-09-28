#!/usr/bin/env python3
"""Free media providers for the Shorts pipeline.

Provider credentials are accepted by callers and are never returned in asset
metadata. Network helpers use bounded timeouts and only HTTP(S) downloads are
accepted.
"""
from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
PIXABAY_SEARCH_URL = "https://pixabay.com/api/videos/"
OPENVERSE_SEARCH_URL = "https://api.openverse.org/v1/images/"
USER_AGENT = "Cerno-Shorts-Free-Media/1.0"


def _now_iso() -> str:
    """Return a compact UTC timestamp for provenance records."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _redact_url(url: str) -> str:
    """Redact sensitive query values from a URL before surfacing it."""
    parts = urlsplit(url)
    redacted = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key.lower() in {"key", "api_key", "apikey", "token", "access_token"}:
            value = "[REDACTED]"
        redacted.append((key, value))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(redacted), parts.fragment))


def _redact_secret(text: str, secret: str | None) -> str:
    """Remove one configured credential from an error string."""
    if secret:
        text = text.replace(secret, "[REDACTED]")
    return text


def _request_json(url: str, *, headers: Mapping[str, str] | None = None, timeout: int = 15) -> Any:
    """Fetch and decode JSON with a bounded timeout and redacted failures."""
    request_headers = {"User-Agent": USER_AGENT}
    if headers:
        request_headers.update(dict(headers))
    request = Request(url, headers=request_headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"request failed: {_redact_url(url)}: {exc}") from exc
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid JSON from {_redact_url(url)}") from exc


def _choose_pexels_file(files: Any) -> str | None:
    """Prefer a portrait, high-resolution Pexels video file."""
    if not isinstance(files, list):
        return None
    candidates: list[tuple[int, int, str]] = []
    for item in files:
        if not isinstance(item, dict):
            continue
        link = item.get("link")
        if not isinstance(link, str) or not link.startswith(("http://", "https://")):
            continue
        try:
            width = int(item.get("width") or 0)
            height = int(item.get("height") or 0)
        except (TypeError, ValueError):
            width = height = 0
        portrait = 1 if height >= width and height > 0 else 0
        candidates.append((portrait, width * height, link))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][2]


def _choose_pixabay_file(videos: Any) -> str | None:
    """Prefer the highest-resolution usable Pixabay video file."""
    if not isinstance(videos, dict):
        return None
    candidates: list[tuple[int, str]] = []
    for item in videos.values():
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            continue
        try:
            width = int(item.get("width") or 0)
            height = int(item.get("height") or 0)
        except (TypeError, ValueError):
            width = height = 0
        candidates.append((width * height, url))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def search_pexels(query: str, api_key: str, *, limit: int = 12) -> list[dict]:
    """Search Pexels videos and normalize usable results."""
    if not isinstance(api_key, str) or not api_key.strip():
        return []
    params = urlencode({"query": query, "per_page": max(1, min(int(limit), 80)), "orientation": "portrait"})
    url = f"{PEXELS_SEARCH_URL}?{params}"
    try:
        payload = _request_json(url, headers={"Authorization": api_key.strip()})
    except RuntimeError as exc:
        raise RuntimeError(_redact_secret(str(exc), api_key)) from exc
    videos = payload.get("videos") if isinstance(payload, dict) else None
    if not isinstance(videos, list):
        return []
    now = _now_iso()
    results: list[dict] = []
    for item in videos:
        if not isinstance(item, dict):
            continue
        download_url = _choose_pexels_file(item.get("video_files"))
        source_url = item.get("url")
        asset_id = item.get("id")
        if not download_url or asset_id is None or not isinstance(source_url, str) or not source_url.startswith(("http://", "https://")):
            continue
        user = item.get("user") if isinstance(item.get("user"), dict) else {}
        creator = user.get("name") if isinstance(user.get("name"), str) else None
        results.append({
            "provider": "pexels",
            "provider_asset_id": str(asset_id),
            "source_url": source_url,
            "download_url": download_url,
            "media_type": "video",
            "license_note": "Pexels License — verify current provider terms at source",
            "creator": creator,
            "retrieved_at": now,
        })
    return results[:limit]


def search_pixabay(query: str, api_key: str, *, limit: int = 12) -> list[dict]:
    """Search Pixabay videos and normalize usable results."""
    if not isinstance(api_key, str) or not api_key.strip():
        return []
    params = urlencode({"key": api_key.strip(), "q": query, "per_page": max(3, min(int(limit), 200)), "safesearch": "true"})
    url = f"{PIXABAY_SEARCH_URL}?{params}"
    try:
        payload = _request_json(url)
    except RuntimeError as exc:
        raise RuntimeError(_redact_secret(str(exc), api_key)) from exc
    hits = payload.get("hits") if isinstance(payload, dict) else None
    if not isinstance(hits, list):
        return []
    now = _now_iso()
    results: list[dict] = []
    for item in hits:
        if not isinstance(item, dict):
            continue
        download_url = _choose_pixabay_file(item.get("videos"))
        source_url = item.get("pageURL")
        asset_id = item.get("id")
        if not download_url or asset_id is None or not isinstance(source_url, str) or not source_url.startswith(("http://", "https://")):
            continue
        creator = item.get("user") if isinstance(item.get("user"), str) else None
        results.append({
            "provider": "pixabay",
            "provider_asset_id": str(asset_id),
            "source_url": source_url,
            "download_url": download_url,
            "media_type": "video",
            "license_note": "Pixabay Content License — verify current provider terms at source",
            "creator": creator,
            "retrieved_at": now,
        })
    return results[:limit]


def search_openverse(query: str, *, limit: int = 12) -> list[dict]:
    """Search Openverse images, keeping only results with explicit license data."""
    params = urlencode({"q": query, "page_size": max(1, min(int(limit), 20))})
    url = f"{OPENVERSE_SEARCH_URL}?{params}"
    payload = _request_json(url)
    items = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return []
    now = _now_iso()
    results: list[dict] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        license_name = item.get("license")
        license_url = item.get("license_url")
        source_url = item.get("foreign_landing_url")
        download_url = item.get("url")
        asset_id = item.get("id")
        if not all(isinstance(value, str) and value.strip() for value in (license_name, license_url, source_url, download_url)):
            continue
        if asset_id is None or not source_url.startswith(("http://", "https://")) or not download_url.startswith(("http://", "https://")):
            continue
        creator = item.get("creator") if isinstance(item.get("creator"), str) else None
        results.append({
            "provider": "openverse",
            "provider_asset_id": str(asset_id),
            "source_url": source_url,
            "download_url": download_url,
            "media_type": "image",
            "license_note": f"{license_name} — {license_url}",
            "creator": creator,
            "retrieved_at": now,
        })
    return results[:limit]


def search_free_media(query: str, *, env: Mapping[str, str] | None = None, limit: int = 12) -> list[dict]:
    """Return the first usable result set from configured free providers."""
    config = os.environ if env is None else env
    providers = []
    pexels_key = config.get("PEXELS_API_KEY")
    pixabay_key = config.get("PIXABAY_API_KEY")
    if pexels_key:
        providers.append(lambda: search_pexels(query, pexels_key, limit=limit))
    if pixabay_key:
        providers.append(lambda: search_pixabay(query, pixabay_key, limit=limit))
    providers.append(lambda: search_openverse(query, limit=limit))
    last_error: RuntimeError | None = None
    for provider in providers:
        try:
            results = provider()
        except RuntimeError as exc:
            last_error = exc
            continue
        if results:
            return results
    if last_error and len(providers) == 1:
        raise last_error
    return []


def download_asset(asset: dict, destination: Path) -> Path:
    """Download one normalized asset to a local file path."""
    url = asset.get("download_url") if isinstance(asset, dict) else None
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        raise ValueError("download_url must use http or https")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=30) as response:
            data = response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise RuntimeError(f"asset download failed: {_redact_url(url)}: {exc}") from exc
    if not data:
        raise RuntimeError("asset download returned no data")
    destination.write_bytes(data)
    return destination
