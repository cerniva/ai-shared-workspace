#!/usr/bin/env python3
"""Prepare and render a zero-paid-credit Short from an approved research packet.

This orchestration layer acquires free/licensed media, writes provenance and
captions, creates a manifest for ``scripts.shorts_render``, and optionally renders
one MP4. It never uploads or publishes content.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.shorts_media import download_asset, search_free_media
from scripts.shorts_render import render
from scripts.shorts_research import gate_packet

SUPPORTED_VISUAL_SUFFIXES = {
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".ppm",
    ".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi",
}
MAX_ASSETS = 3


def default_espeak_voice(language: str, explicit_voice: str | None = None) -> str:
    if isinstance(explicit_voice, str) and explicit_voice.strip():
        return explicit_voice.strip()
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language is required for narration_voice selection")
    normalized = language.strip().lower().replace("_", "-")
    if normalized == "tr" or normalized.startswith("tr-"):
        return "tr"
    if normalized == "en" or normalized.startswith("en-"):
        return "en-us"
    raise ValueError(f"narration_voice is required for unsupported automatic language mapping: {language}")


def _srt_time(seconds: float) -> str:
    millis = max(0, int(round(seconds * 1000)))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _caption_chunks(text: str, max_chars: int) -> list[str]:
    if max_chars < 8:
        raise ValueError("max_chars must be at least 8")
    words = re.findall(r"\S+", text.strip())
    if not words:
        raise ValueError("caption text must be non-empty")
    chunks: list[str] = []
    current = ""
    for word in words:
        if len(word) > max_chars:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(word)
            continue
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


def build_srt(text: str, target_seconds: float, *, max_chars: int = 42) -> str:
    try:
        duration = float(target_seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError("target_seconds must be a number") from exc
    if duration <= 0:
        raise ValueError("target_seconds must be positive")
    chunks = _caption_chunks(text, max_chars)
    slot = duration / len(chunks)
    entries = []
    for index, chunk in enumerate(chunks, start=1):
        start = (index - 1) * slot
        end = duration if index == len(chunks) else index * slot
        entries.append(f"{index}\n{_srt_time(start)} --> {_srt_time(end)}\n{chunk}\n")
    return "\n".join(entries)


def _asset_suffix(asset: dict) -> str:
    url = asset.get("download_url") if isinstance(asset, dict) else None
    suffix = ""
    if isinstance(url, str):
        suffix = Path(urlsplit(url).path).suffix.lower()
    if suffix in SUPPORTED_VISUAL_SUFFIXES:
        return suffix
    return ".mp4" if asset.get("media_type") == "video" else ".jpg"


def _load_packet(packet_path: Path) -> dict:
    path = Path(packet_path)
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("packet is not valid JSON") from exc
    if not isinstance(packet, dict):
        raise ValueError("packet must be a JSON object")
    return packet


def prepare_render_bundle(packet_path: Path, workdir: Path, *, env: Mapping[str, str] | None = None) -> dict:
    packet = _load_packet(Path(packet_path))
    blockers = gate_packet(packet)
    if blockers:
        raise ValueError("research gate blocked: " + ",".join(blockers))

    try:
        target_seconds = float(packet["target_seconds"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("target_seconds must be a number") from exc
    if target_seconds <= 0 or target_seconds > 180:
        raise ValueError("target_seconds must be between 0 and 180 seconds")

    queries = [q.strip() for q in packet.get("media_queries", []) if isinstance(q, str) and q.strip()]
    if not queries:
        raise ValueError("research gate blocked: missing_media_queries")

    workdir = Path(workdir).resolve()
    asset_dir = workdir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)

    selected: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for query in queries:
        results = search_free_media(query, env=env, limit=6)
        for item in results:
            if not isinstance(item, dict):
                continue
            provider = item.get("provider")
            asset_id = item.get("provider_asset_id")
            if not isinstance(provider, str) or not isinstance(asset_id, str):
                continue
            identity = (provider, asset_id)
            if identity in seen:
                continue
            seen.add(identity)
            selected.append(dict(item))
            if len(selected) >= MAX_ASSETS:
                break
        if len(selected) >= MAX_ASSETS:
            break

    if not selected:
        raise RuntimeError("no usable free media asset found")

    local_assets: list[Path] = []
    for index, item in enumerate(selected, start=1):
        destination = asset_dir / f"asset-{index:02d}{_asset_suffix(item)}"
        downloaded = Path(download_asset(item, destination)).resolve()
        if downloaded.parent != asset_dir or not downloaded.is_file():
            raise RuntimeError("downloaded asset escaped the bundle directory or is missing")
        local_assets.append(downloaded)

    provenance_path = workdir / "provenance.json"
    provenance_path.write_text(json.dumps(selected, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    captions_path = workdir / "captions.srt"
    captions_path.write_text(build_srt(packet["narration_text"], target_seconds), encoding="utf-8")

    voice = default_espeak_voice(packet["language"], packet.get("narration_voice"))
    base_duration = target_seconds / len(local_assets)
    durations = [base_duration] * len(local_assets)
    durations[-1] = target_seconds - sum(durations[:-1])
    visuals = [
        {"path": asset.relative_to(workdir).as_posix(), "duration": round(duration, 6)}
        for asset, duration in zip(local_assets, durations)
    ]

    render_manifest_path = workdir / "render.json"
    manifest = {
        "target_seconds": target_seconds,
        "visuals": visuals,
        "narration_text": packet["narration_text"].strip(),
        "narration_voice": voice,
        "narration_speed": int(packet.get("narration_speed", 165)),
        "subtitles": captions_path.relative_to(workdir).as_posix(),
    }
    render_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return {
        "render_manifest": str(render_manifest_path),
        "provenance": str(provenance_path),
        "captions": str(captions_path),
        "assets": [str(path) for path in local_assets],
        "language": packet["language"],
        "content_type": packet["content_type"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("workdir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        bundle = prepare_render_bundle(args.packet, args.workdir)
        result = render(Path(bundle["render_manifest"]), args.output)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, "bundle": bundle, "render": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
