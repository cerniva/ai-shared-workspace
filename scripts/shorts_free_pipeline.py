#!/usr/bin/env python3
"""Prepare a zero-credit Shorts render bundle from an approved research packet."""
from __future__ import annotations

import argparse
import json
import re
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit

from scripts.shorts_media import download_asset, search_free_media
from scripts.shorts_research import gate_packet
from scripts.shorts_render import render

VOICE_RE = re.compile(r"^[A-Za-z0-9_.+\-]{1,64}$")


def default_espeak_voice(language: str, explicit_voice: str | None = None) -> str:
    """Map validated packet languages to eSpeak voices, or require an explicit voice."""
    if explicit_voice is not None:
        if not isinstance(explicit_voice, str) or not VOICE_RE.fullmatch(explicit_voice.strip()):
            raise ValueError("narration_voice contains unsupported characters")
        return explicit_voice.strip()
    if not isinstance(language, str) or not language.strip():
        raise ValueError("language is required")
    normalized = language.strip().lower()
    if normalized == "tr" or normalized.startswith("tr-"):
        return "tr"
    if normalized == "en" or normalized.startswith("en-"):
        return "en-us"
    raise ValueError("narration_voice is required for unsupported language")


def _srt_timestamp(seconds: float) -> str:
    milliseconds = max(0, int(round(seconds * 1000)))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _chunk_text(text: str, max_chars: int) -> list[str]:
    words = text.split()
    if not words:
        raise ValueError("caption text must not be empty")
    if max_chars < 8:
        raise ValueError("max_chars must be at least 8")
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
    """Build evenly-timed mobile-readable SRT captions from known narration text."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("narration_text is required for captions")
    try:
        duration = float(target_seconds)
    except (TypeError, ValueError) as exc:
        raise ValueError("target_seconds must be a number") from exc
    if duration <= 0:
        raise ValueError("target_seconds must be positive")
    chunks = _chunk_text(text.strip(), max_chars)
    step = duration / len(chunks)
    blocks = []
    for index, chunk in enumerate(chunks, start=1):
        start = (index - 1) * step
        end = duration if index == len(chunks) else index * step
        blocks.append(
            f"{index}\n{_srt_timestamp(start)} --> {_srt_timestamp(end)}\n{chunk}\n"
        )
    return "\n".join(blocks)


def _asset_extension(asset: dict) -> str:
    path = urlsplit(str(asset.get("download_url") or "")).path
    suffix = Path(path).suffix.lower()
    if suffix and re.fullmatch(r"\.[a-z0-9]{2,5}", suffix):
        return suffix
    return ".mp4" if asset.get("media_type") == "video" else ".jpg"


def prepare_render_bundle(
    packet_path: Path,
    workdir: Path,
    *,
    env: Mapping[str, str] | None = None,
) -> dict:
    """Validate a packet, acquire up to three assets, and write local render inputs."""
    packet_path = Path(packet_path)
    if not packet_path.is_file():
        raise ValueError(f"packet does not exist: {packet_path}")
    try:
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("packet is not valid JSON") from exc
    blockers = gate_packet(packet)
    if blockers:
        raise ValueError("research gate blocked: " + ",".join(blockers))

    workdir = Path(workdir)
    assets_dir = workdir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    selected: list[dict] = []
    seen: set[tuple[str, str]] = set()
    queries = [
        value.strip()
        for value in packet.get("media_queries", [])
        if isinstance(value, str) and value.strip()
    ]
    for query in queries:
        for item in search_free_media(query, env=env, limit=6):
            if not isinstance(item, dict):
                continue
            key = (str(item.get("provider") or ""), str(item.get("provider_asset_id") or ""))
            if not all(key) or key in seen:
                continue
            seen.add(key)
            selected.append(dict(item))
            if len(selected) >= 3:
                break
        if len(selected) >= 3:
            break
    if not selected:
        raise RuntimeError("no usable free media assets found")

    local_assets: list[Path] = []
    for index, item in enumerate(selected, start=1):
        destination = assets_dir / f"asset-{index:03d}{_asset_extension(item)}"
        local_assets.append(Path(download_asset(item, destination)))

    provenance_path = workdir / "provenance.json"
    provenance_path.write_text(
        json.dumps(selected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    target_seconds = float(packet["target_seconds"])
    captions_path = workdir / "captions.srt"
    captions_path.write_text(
        build_srt(packet["narration_text"], target_seconds),
        encoding="utf-8",
    )

    voice = default_espeak_voice(packet["language"], packet.get("narration_voice"))
    count = len(local_assets)
    segment_seconds = target_seconds / count
    visuals = []
    for index, path in enumerate(local_assets):
        duration = (
            target_seconds - segment_seconds * (count - 1)
            if index == count - 1
            else segment_seconds
        )
        visuals.append({
            "path": path.relative_to(workdir).as_posix(),
            "duration": round(duration, 6),
        })

    manifest = {
        "target_seconds": target_seconds,
        "visuals": visuals,
        "narration_text": packet["narration_text"].strip(),
        "narration_voice": voice,
        "narration_speed": int(packet.get("narration_speed", 165)),
        "subtitles": captions_path.relative_to(workdir).as_posix(),
    }
    manifest_path = workdir / "render.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "render_manifest": manifest_path,
        "provenance": provenance_path,
        "captions": captions_path,
        "assets": local_assets,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("workdir", type=Path)
    parser.add_argument("output_mp4", type=Path)
    args = parser.parse_args()
    try:
        bundle = prepare_render_bundle(args.packet, args.workdir)
        result = render(Path(bundle["render_manifest"]), args.output_mp4)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    printable = {key: [str(p) for p in value] if key == "assets" else str(value) for key, value in bundle.items()}
    print(json.dumps({"ok": True, "bundle": printable, "render": result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
