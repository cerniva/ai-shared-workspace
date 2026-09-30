#!/usr/bin/env python3
"""Production-safe free-first Shorts entrypoint.

This wrapper hardens shorts_free_pipeline by refusing still-image media before
bundle preparation. It exists so production cannot silently fall back to an
Openverse image/slideshow when free video providers are unavailable.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts import shorts_free_pipeline as pipeline
from scripts.shorts_media import search_free_media as _search_free_media


def search_video_only(query: str, *, env=None, limit: int = 12) -> list[dict]:
    """Return only normalized real-video assets; fail closed otherwise."""
    results = _search_free_media(query, env=env, limit=limit)
    videos = [
        dict(item)
        for item in results
        if isinstance(item, dict) and item.get("media_type") == "video"
    ]
    if not videos:
        raise RuntimeError(
            "production_video_only_gate: no rights-traceable moving-video asset found; "
            "still-image/slideshow fallback is disabled"
        )
    return videos


def prepare_render_bundle(packet_path: Path, workdir: Path, *, env=None) -> dict:
    """Prepare using the existing pipeline with a fail-closed video-only gate."""
    original = pipeline.search_free_media
    pipeline.search_free_media = search_video_only
    try:
        bundle = pipeline.prepare_render_bundle(packet_path, workdir, env=env)
    finally:
        pipeline.search_free_media = original

    assets = bundle.get("assets", [])
    if not assets:
        raise RuntimeError("production_video_only_gate: bundle contains no assets")
    image_suffixes = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".ppm"}
    if any(Path(asset).suffix.lower() in image_suffixes for asset in assets):
        raise RuntimeError("production_video_only_gate: still image reached production bundle")
    bundle["production_video_only"] = True
    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("packet", type=Path)
    parser.add_argument("workdir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        bundle = prepare_render_bundle(args.packet, args.workdir)
        result = pipeline.render(Path(bundle["render_manifest"]), args.output)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "ready": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, "ready": False, "bundle": bundle, "render": result, "note": "rendered; independent QA/preflight still required"}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
