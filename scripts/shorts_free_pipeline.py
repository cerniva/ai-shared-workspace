#!/usr/bin/env python3
"""Prepare free-first Shorts render bundles and optionally invoke the local renderer.

This module performs no publishing. It validates an approved research packet,
acquires free media through the shared provider layer, writes provenance and
captions, prepares a local-only manifest, and delegates final MP4 creation to
`scripts.shorts_render`.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from scripts.shorts_media import download_asset, search_free_media
from scripts.shorts_render import render
from scripts.shorts_research import gate_packet, load_json


_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def default_espeak_voice(language: str, explicit_voice: str | None = None) -> str:
    """Return a validated local eSpeak voice for supported language families."""
    if explicit_voice:
        return explicit_voice.strip()
    normalized = (language or "").strip().lower()
    if normalized.startswith("tr"):
        return "tr"
    if normalized.startswith("en"):
        return "en-us"
    raise ValueError("unsupported language requires narration_voice")


def _chunks(text: str, max_chars: int) -> list[str]:
    """Split narration into readable caption chunks without dropping words."""
    words = text.strip().split()
    if not words:
        raise ValueError("narration_text must not be empty")
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            chunks.append(current)
            current = ""
        if len(word) <= max_chars:
            current = word
        else:
            for start in range(0, len(word), max_chars):
                part = word[start : start + max_chars]
                if len(part) == max_chars:
                    chunks.append(part)
                else:
                    current = part
    if current:
        chunks.append(current)
    return chunks


def _srt_time(seconds: float) -> str:
    """Format seconds as an SRT timestamp."""
    millis = max(0, round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def build_srt(text: str, target_seconds: float, *, max_chars: int = 42) -> str:
    """Build evenly timed, mobile-readable SRT captions from known narration text."""
    if target_seconds <= 0:
        raise ValueError("target_seconds must be positive")
    if max_chars < 8:
        raise ValueError("max_chars is too small")
    chunks = _chunks(text, max_chars)
    duration = target_seconds / len(chunks)
    blocks = []
    for index, chunk in enumerate(chunks, start=1):
        start = (index - 1) * duration
        end = target_seconds if index == len(chunks) else index * duration
        blocks.append(f"{index}\n{_srt_time(start)} --> {_srt_time(end)}\n{chunk}\n")
    return "\n".join(blocks)


def _asset_suffix(asset: dict) -> str:
    """Choose a conservative local suffix from normalized media metadata."""
    parsed = urlparse(str(asset.get("download_url") or ""))
    suffix = Path(parsed.path).suffix.lower()
    if asset.get("media_type") == "image":
        return suffix if suffix in {".jpg", ".jpeg", ".png", ".webp"} else ".jpg"
    return suffix if suffix in {".mp4", ".mov", ".mkv", ".webm"} else ".mp4"


def _asset_key(asset: dict) -> tuple[str, str]:
    """Return a stable in-bundle dedup key without exposing credentials."""
    provider = str(asset.get("provider") or "")
    identity = str(asset.get("provider_asset_id") or asset.get("download_url") or "")
    return provider, identity


def prepare_render_bundle(
    packet_path: Path,
    workdir: Path,
    *,
    env: Mapping[str, str] | None = None,
) -> dict:
    """Validate a packet and prepare local assets, provenance, captions, and manifest."""
    packet_path = Path(packet_path).resolve()
    packet = load_json(packet_path)
    blockers = gate_packet(packet)
    if blockers:
        raise ValueError("research packet blocked: " + ", ".join(blockers))
    if packet.get("free_render_requested") is not True:
        raise ValueError("free_render_requested must be true")

    target_seconds = float(packet["target_seconds"])
    voice = default_espeak_voice(packet["language"], packet.get("narration_voice"))
    workdir = Path(workdir).resolve()
    assets_dir = workdir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    queries: list[str] = []
    seen_queries: set[str] = set()
    for raw in packet["media_queries"]:
        query = raw.strip()
        key = query.casefold()
        if key not in seen_queries:
            seen_queries.add(key)
            queries.append(query)

    selected: list[dict] = []
    seen_assets: set[tuple[str, str]] = set()
    for query in queries:
        results = search_free_media(query, env=env, limit=12)
        for asset in results:
            key = _asset_key(asset)
            if not key[1] or key in seen_assets:
                continue
            seen_assets.add(key)
            selected.append(dict(asset))
            break
        if len(selected) >= 3:
            break
    if not selected:
        raise ValueError("no usable free media found")

    local_assets: list[Path] = []
    for index, asset in enumerate(selected, start=1):
        destination = assets_dir / f"asset-{index:02d}{_asset_suffix(asset)}"
        download_asset(asset, destination)
        if not destination.is_file():
            raise RuntimeError(f"media provider did not create asset: {destination.name}")
        local_assets.append(destination)

    provenance_path = workdir / "provenance.json"
    provenance_path.write_text(
        json.dumps({"packet_id": packet.get("id"), "assets": selected}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    captions_path = workdir / "captions.srt"
    captions_path.write_text(build_srt(packet["narration_text"], target_seconds), encoding="utf-8")

    segment = target_seconds / len(local_assets)
    visuals = []
    elapsed = 0.0
    for index, path in enumerate(local_assets):
        duration = target_seconds - elapsed if index == len(local_assets) - 1 else segment
        visuals.append({"path": path.relative_to(workdir).as_posix(), "duration": duration})
        elapsed += duration

    manifest_path = workdir / "render.json"
    manifest = {
        "target_seconds": target_seconds,
        "visuals": visuals,
        "narration_text": packet["narration_text"].strip(),
        "narration_voice": voice,
        "subtitles": captions_path.relative_to(workdir).as_posix(),
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "render_manifest": str(manifest_path),
        "provenance": str(provenance_path),
        "captions": str(captions_path),
        "assets": [str(path) for path in local_assets],
    }


def main() -> int:
    """Prepare a free render bundle, invoke the local renderer, and print metadata."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("workdir", type=Path)
    parser.add_argument("output_mp4", type=Path)
    args = parser.parse_args()
    try:
        bundle = prepare_render_bundle(args.packet, args.workdir)
        result = render(Path(bundle["render_manifest"]), args.output_mp4)
    except (OSError, RuntimeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, "bundle": bundle, "render": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
