#!/usr/bin/env python3
"""Free-first media acquisition helpers for Shorts production.

Pexels and Pixabay provide video search when their API keys are configured.
Openverse is the no-secret fallback for explicitly licensed images only.
Provider credentials are never included in returned asset records or errors.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.request import Request, urlopen

PEXELS_VIDEO_SEARCH = "https://api.pexels.com/v1/videos/search"
PIXABAY_VIDEO_SEARCH = "https://pixabay.com/api/videos/"
OPENVERSE_IMAGE_SEARCH = "https://api.openverse.org/v1/images/"
DEFAULT_TIMEOUT = 15
DEFAULT_API_HEADERS = {
    "User-Agent": "cerniva-shorts-media/1.0 (+https://github.com/cerniva/ai-shared-workspace)",
    "Accept": "application/json",
}


class MediaProviderError(RuntimeError):
    """Raised when a media provider request cannot be used safely."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _redact_url(url: str) -> str:
    """Redact credential-like query parameters from a URL before surfacing it."""
    try:
        parsed = urlparse(url)
        redacted = []
        for key, value in parse_qsl(parsed.query, keep_blank_values=True):
            if key.casefold() in {"key", "api_key", "apikey", "token", "access_token"}:
                value = "[REDACTED]"
            redacted.append((key, value))
        return urlunparse(parsed._replace(query=urlencode(redacted)))
    except Exception:
        return url


def _request_json(url: str, *, headers: Mapping[str, str] | None = None, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Fetch one JSON object with a bounded timeout."""
    request_headers = {**DEFAULT_API_HEADERS, **dict(headers or {})}
    request = Request(url, headers=request_headers)
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = response.read()
    except Exception as exc:
        raise RuntimeError(f"request failed: {_redact_url(url)}") from exc
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"invalid JSON response: {_redact_url(url)}") from exc
    if not isinstance(data, dict):
        raise RuntimeError(f"unexpected JSON payload: {_redact_url(url)}")
    return data


def _download_bytes(url: str, *, timeout: int = DEFAULT_TIMEOUT) -> bytes:
    """Download bytes from an unauthenticated HTTP(S) asset URL."""
    request = Request(url, headers={"User-Agent": "cerniva-shorts-media/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.read()
    except Exception as exc:
        raise MediaProviderError(f"asset download failed: {_redact_url(url)}") from exc


def _best_video_file(files) -> str | None:
    """Return the largest usable HTTP(S) video URL from provider renditions."""
    candidates: list[tuple[int, str]] = []
    iterable = files.values() if isinstance(files, dict) else files if isinstance(files, list) else []
    for item in iterable:
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("link")
        parsed = urlparse(url) if isinstance(url, str) else None
        if not parsed or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue
        try:
            area = int(item.get("width") or 0) * int(item.get("height") or 0)
        except (TypeError, ValueError):
            area = 0
        candidates.append((area, url))
    return max(candidates, default=(0, None), key=lambda value: value[0])[1]


def search_pexels(query: str, api_key: str, *, limit: int = 12) -> list[dict]:
    """Search Pexels videos and normalize valid results into media assets."""
    params = urlencode({"query": query, "per_page": limit})
    url = f"{PEXELS_VIDEO_SEARCH}?{params}"
    try:
        payload = _request_json(url, headers={"Authorization": api_key})
    except Exception as exc:
        message = str(exc).replace(api_key, "[REDACTED]") if api_key else str(exc)
        raise MediaProviderError(message) from exc
    videos = payload.get("videos")
    if not isinstance(videos, list):
        return []
    retrieved_at = _utc_now()
    assets = []
    for item in videos[:limit]:
        if not isinstance(item, dict):
            continue
        download_url = _best_video_file(item.get("video_files"))
        source_url = item.get("url")
        asset_id = item.get("id")
        if download_url is None or not source_url or asset_id is None:
            continue
        user = item.get("user")
        creator = user.get("name") if isinstance(user, dict) else None
        assets.append(
            {
                "provider": "pexels",
                "provider_asset_id": str(asset_id),
                "source_url": str(source_url),
                "download_url": download_url,
                "media_type": "video",
                "license_note": "Pexels License: https://www.pexels.com/license/",
                "creator": creator,
                "retrieved_at": retrieved_at,
            }
        )
    return assets


def search_pixabay(query: str, api_key: str, *, limit: int = 12) -> list[dict]:
    """Search Pixabay videos and normalize valid results without leaking the key."""
    params = urlencode({"key": api_key, "q": query, "per_page": limit})
    url = f"{PIXABAY_VIDEO_SEARCH}?{params}"
    try:
        payload = _request_json(url)
    except Exception as exc:
        message = str(exc).replace(api_key, "[REDACTED]") if api_key else str(exc)
        raise MediaProviderError(message) from exc
    hits = payload.get("hits")
    if not isinstance(hits, list):
        return []
    retrieved_at = _utc_now()
    assets = []
    for item in hits[:limit]:
        if not isinstance(item, dict):
            continue
        download_url = _best_video_file(item.get("videos"))
        source_url = item.get("pageURL")
        asset_id = item.get("id")
        if download_url is None or not source_url or asset_id is None:
            continue
        assets.append(
            {
                "provider": "pixabay",
                "provider_asset_id": str(asset_id),
                "source_url": str(source_url),
                "download_url": download_url,
                "media_type": "video",
                "license_note": "Pixabay Content License: https://pixabay.com/service/license-summary/",
                "creator": item.get("user") or None,
                "retrieved_at": retrieved_at,
            }
        )
    return assets


def search_openverse(query: str, *, limit: int = 12) -> list[dict]:
    """Search Openverse images and keep only records with explicit license metadata."""
    params = urlencode({"q": query, "page_size": limit})
    url = f"{OPENVERSE_IMAGE_SEARCH}?{params}"
    try:
        payload = _request_json(url)
    except Exception as exc:
        raise MediaProviderError(str(exc)) from exc
    results = payload.get("results")
    if not isinstance(results, list):
        return []
    retrieved_at = _utc_now()
    assets = []
    for item in results[:limit]:
        if not isinstance(item, dict):
            continue
        asset_id = item.get("id")
        download_url = item.get("url")
        source_url = item.get("foreign_landing_url")
        license_code = item.get("license")
        license_url = item.get("license_url")
        parsed = urlparse(download_url) if isinstance(download_url, str) else None
        if (
            asset_id is None
            or not parsed
            or parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or not source_url
            or not license_code
            or not license_url
        ):
            continue
        assets.append(
            {
                "provider": "openverse",
                "provider_asset_id": str(asset_id),
                "source_url": str(source_url),
                "download_url": download_url,
                "media_type": "image",
                "license_note": f"{license_code}: {license_url}",
                "creator": item.get("creator") or None,
                "retrieved_at": retrieved_at,
            }
        )
    return assets


def search_free_media(
    query: str,
    *,
    env: Mapping[str, str] | None = None,
    limit: int = 12,
) -> list[dict]:
    """Try configured free providers in order, falling back without blind retries."""
    values = os.environ if env is None else env
    failures: list[str] = []
    pexels_key = values.get("PEXELS_API_KEY")
    pixabay_key = values.get("PIXABAY_API_KEY")

    if pexels_key:
        try:
            assets = search_pexels(query, pexels_key, limit=limit)
            if assets:
                return assets
        except MediaProviderError as exc:
            failures.append(f"pexels: {exc}")

    if pixabay_key:
        try:
            assets = search_pixabay(query, pixabay_key, limit=limit)
            if assets:
                return assets
        except MediaProviderError as exc:
            failures.append(f"pixabay: {exc}")

    try:
        assets = search_openverse(query, limit=limit)
        if assets:
            return assets
    except MediaProviderError as exc:
        failures.append(f"openverse: {exc}")

    if failures:
        raise MediaProviderError("; ".join(failures))
    return []


def download_asset(asset: dict, destination: Path) -> Path:
    """Download one normalized asset to a local path using an atomic replace."""
    url = asset.get("download_url") if isinstance(asset, dict) else None
    parsed = urlparse(url) if isinstance(url, str) else None
    if not parsed or parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("download_url must be an absolute HTTP(S) URL")

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = _download_bytes(url)
    if not payload:
        raise MediaProviderError("asset download returned no data")

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as handle:
            handle.write(payload)
            handle.flush()
            temp_path = Path(handle.name)
        temp_path.replace(destination)
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()
    return destination
