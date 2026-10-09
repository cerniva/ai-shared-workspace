#!/usr/bin/env python3
"""Prepare and render a zero-paid-credit Short from an approved research packet.

This orchestration layer acquires free/licensed media, writes provenance and
captions, creates a manifest for ``scripts.shorts_render``, and renders one MP4.
It never uploads or publishes content.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
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
from scripts import shorts_learnings

SUPPORTED_VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".ppm"}
MAX_ASSETS = 3
VOICE_RE = re.compile(r"^[A-Za-z0-9_.+\-]{1,64}$")


def default_espeak_voice(language: str, explicit_voice: str | None = None) -> str:
    """Choose a validated local eSpeak voice for a packet language."""
    if explicit_voice is not None:
        if not isinstance(explicit_voice, str) or not VOICE_RE.fullmatch(explicit_voice.strip()):
            raise ValueError("narration_voice contains unsupported characters")
        return explicit_voice.strip()
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language is required for narration_voice selection")
    normalized = language.strip().lower().replace("_", "-")
    if normalized == "tr" or normalized.startswith("tr-"):
        return "tr"
    if normalized == "en" or normalized.startswith("en-"):
        return "en-us"
    raise ValueError(
        f"narration_voice is required for unsupported automatic language mapping: {language}"
    )


def _srt_time(seconds: float) -> str:
    """Format seconds as an SRT timestamp."""
    millis = max(0, int(round(seconds * 1000)))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _caption_chunks(text: str, max_chars: int) -> list[str]:
    """Split narration into mobile-readable word-preserving caption chunks."""
    if max_chars < 8:
        raise ValueError("max_chars must be at least 8")
    words = re.findall(r"\S+", text.strip())
    if not words:
        raise ValueError("caption text must be non-empty")
    chunks: list[str] = []
    current = ""
    for word in words:
        if len(word) > max_chars:
            raise ValueError("caption word exceeds max_chars")
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
    """Build evenly timed SRT captions from known narration text."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("narration_text is required for captions")
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
        entries.append(
            f"{index}\n{_srt_time(start)} --> {_srt_time(end)}\n{chunk}\n"
        )
    return "\n".join(entries)


def _is_video_asset(item: dict) -> bool:
    return isinstance(item, dict) and item.get("media_type") == "video"


def _asset_suffix(asset: dict) -> str:
    """Derive a renderer-compatible video suffix without trusting URL queries."""
    if not _is_video_asset(asset):
        raise ValueError("production Short requires real video assets; still image rejected")
    url = asset.get("download_url")
    suffix = ""
    if isinstance(url, str):
        suffix = Path(urlsplit(url).path).suffix.lower()
    return suffix if suffix in SUPPORTED_VIDEO_SUFFIXES else ".mp4"


def _probe_real_video(path: Path) -> None:
    """Fail closed unless ffprobe reports a usable non-attached video stream."""
    try:
        proc = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "V:0",
                "-show_entries", "stream=codec_type,width,height",
                "-of", "json",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError("downloaded production asset could not be content-probed") from exc
    if proc.returncode != 0:
        raise RuntimeError("downloaded production asset is not recognized as video content")
    try:
        payload = json.loads(proc.stdout)
        streams = payload.get("streams", [])
    except (json.JSONDecodeError, AttributeError) as exc:
        raise RuntimeError("downloaded production asset returned invalid probe metadata") from exc
    if not any(
        isinstance(stream, dict)
        and stream.get("codec_type") == "video"
        and int(stream.get("width") or 0) > 0
        and int(stream.get("height") or 0) > 0
        for stream in streams
    ):
        raise RuntimeError("downloaded production asset has no usable moving-video stream")


def _asset_identity(item: dict) -> tuple[str, str] | None:
    """Return a stable provider identity for a normalized asset."""
    if not isinstance(item, dict):
        return None
    provider = item.get("provider")
    asset_id = item.get("provider_asset_id")
    if not isinstance(provider, str) or not isinstance(asset_id, str):
        return None
    return provider, asset_id


def _load_packet(packet_path: Path) -> dict:
    """Load a packet and require a JSON object."""
    path = Path(packet_path)
    if not path.is_file():
        raise ValueError(f"packet does not exist: {path}")
    try:
        packet = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("packet is not valid JSON") from exc
    if not isinstance(packet, dict):
        raise ValueError("packet must be a JSON object")
    return packet


def prepare_render_bundle(
    packet_path: Path,
    workdir: Path,
    *,
    env: Mapping[str, str] | None = None,
    learnings_path: Path | None = None,
) -> dict:
    """Turn one gate-approved packet into local media, provenance and render files.

    With learnings_path, plan learnings are validated before any media is fetched
    and applied to the render manifest (applied_learning_ids recorded).
    """
    packet = _load_packet(Path(packet_path))
    blockers = gate_packet(packet)
    if blockers:
        raise ValueError("research gate blocked: " + ",".join(blockers))
    learnings_doc = shorts_learnings.load(learnings_path) if learnings_path is not None else None

    try:
        target_seconds = float(packet["target_seconds"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("target_seconds must be a number") from exc
    if target_seconds <= 0 or target_seconds > 180:
        raise ValueError("target_seconds must be between 0 and 180 seconds")
    if learnings_doc is not None:
        # fail fast on learning constraints (e.g. 30s cap) before downloading media
        shorts_learnings.apply(learnings_doc, packet, {"target_seconds": target_seconds})

    queries = [
        query.strip()
        for query in packet.get("media_queries", [])
        if isinstance(query, str) and query.strip()
    ]
    if not queries:
        raise ValueError("research gate blocked: missing_media_queries")

    workdir = Path(workdir).resolve()
    asset_dir = workdir / "assets"
    asset_dir.mkdir(parents=True, exist_ok=True)

    selected: list[dict] = []
    seen: set[tuple[str, str]] = set()
    result_sets: list[list[dict]] = []
    provider_failures: list[str] = []
    for query in queries[:MAX_ASSETS]:
        try:
            results = search_free_media(query, env=env, limit=6)
        except RuntimeError as exc:
            provider_failures.append(f"{query}: {exc}")
            results = []
        videos = [
            dict(item)
            for item in results
            if _is_video_asset(item)
        ] if isinstance(results, list) else []
        result_sets.append(videos)

    # First preserve the packet's intended visual variety: at most one unique
    # asset from each planned query before any query can consume extra slots.
    for results in result_sets:
        for item in results:
            identity = _asset_identity(item)
            if identity is None or identity in seen:
                continue
            seen.add(identity)
            selected.append(dict(item))
            break
        if len(selected) >= MAX_ASSETS:
            break

    # Then fill any remaining slots deterministically in query/result order.
    if len(selected) < MAX_ASSETS:
        for results in result_sets:
            for item in results:
                identity = _asset_identity(item)
                if identity is None or identity in seen:
                    continue
                seen.add(identity)
                selected.append(dict(item))
                if len(selected) >= MAX_ASSETS:
                    break
            if len(selected) >= MAX_ASSETS:
                break

    if not selected:
        detail = "; ".join(provider_failures)
        if detail:
            raise RuntimeError("no usable free VIDEO asset found; provider failures: " + detail)
        raise RuntimeError("no usable free VIDEO asset found; still-image fallback is disabled")

    local_assets: list[Path] = []
    for index, item in enumerate(selected, start=1):
        destination = asset_dir / f"asset-{index:02d}{_asset_suffix(item)}"
        downloaded = Path(download_asset(item, destination)).resolve()
        if downloaded.parent != asset_dir or not downloaded.is_file():
            raise RuntimeError("downloaded asset escaped the bundle directory or is missing")
        if downloaded.suffix.lower() not in SUPPORTED_VIDEO_SUFFIXES or downloaded.suffix.lower() in IMAGE_SUFFIXES:
            raise RuntimeError("downloaded production asset is not a supported video file")
        _probe_real_video(downloaded)
        local_assets.append(downloaded)

    provenance_path = workdir / "provenance.json"
    provenance_path.write_text(
        json.dumps(selected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    captions_path = workdir / "captions.srt"
    captions_path.write_text(
        build_srt(packet["narration_text"], target_seconds),
        encoding="utf-8",
    )

    voice = default_espeak_voice(packet["language"], packet.get("narration_voice"))
    base_duration = target_seconds / len(local_assets)
    durations = [base_duration] * len(local_assets)
    durations[-1] = target_seconds - sum(durations[:-1])
    visuals = [
        {
            "path": asset.relative_to(workdir).as_posix(),
            "duration": round(duration, 6),
        }
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
        "production_gates": {
            "video_only": True,
            "content_probe": "ffprobe",
            "speech_sync_review_required": True,
            "natural_voice_review_required": True,
        },
    }
    applied: list[str] = []
    if learnings_doc is not None:
        applied = shorts_learnings.apply(learnings_doc, packet, manifest)
    render_manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    return {
        "render_manifest": str(render_manifest_path),
        "provenance": str(provenance_path),
        "captions": str(captions_path),
        "assets": [str(path) for path in local_assets],
        "language": packet["language"],
        "content_type": packet["content_type"],
        "applied_learning_ids": applied,
        "upload_policy": manifest.get("upload_policy"),
    }


def main() -> int:
    """Prepare one free render bundle and invoke the existing local renderer."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("workdir", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--learnings", type=Path, required=True,
                        help="plan_learnings.json from scripts/plan_learnings.py video_shopify")
    args = parser.parse_args()
    try:
        bundle = prepare_render_bundle(args.packet, args.workdir, learnings_path=args.learnings)
        result = render(Path(bundle["render_manifest"]), args.output)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, "bundle": bundle, "render": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
