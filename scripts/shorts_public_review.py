"""Fail-closed human PUBLIC approval bound to the exact MP4 bytes.

This check is deliberately separate from the technical preflight. Passing a
render/technical QA gate never implies permission to publish publicly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_CHECKS = (
    "speech_intelligible", "audio_visual_sync", "text_readable",
    "hook_storyboard_checked", "moving_footage_checked",
    "facts_verified", "rights_checked", "correct_channel", "duplicate_checked",
)


def validate_public_review(video: Path, review: Path, root: Path) -> dict:
    root, video, review = root.resolve(), video.resolve(), review.resolve()
    if not video.is_file() or video.suffix.lower() != ".mp4":
        raise ValueError("video must be an existing MP4")
    if not review.is_relative_to(root) or not review.is_file() or review.suffix.lower() != ".json":
        raise ValueError("review must be an existing repository-relative JSON file")
    try:
        data = json.loads(review.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("review JSON missing or invalid") from exc
    if not isinstance(data, dict):
        raise ValueError("review JSON must be an object")
    if data.get("approval_scope") != "PUBLIC":
        raise ValueError("review must explicitly authorize PUBLIC publication")
    if not isinstance(data.get("reviewer"), str) or not data["reviewer"].strip():
        raise ValueError("reviewer identity missing")
    if not isinstance(data.get("reviewed_at"), str) or not data["reviewed_at"].strip():
        raise ValueError("review date missing")
    digest = hashlib.sha256()
    with video.open("rb") as src:
        for chunk in iter(lambda: src.read(1024 * 1024), b""):
            digest.update(chunk)
    actual_sha = digest.hexdigest()
    if data.get("sha256") != actual_sha:
        raise ValueError("review SHA-256 does not match exact MP4")
    checks = data.get("checks")
    if not isinstance(checks, dict):
        raise ValueError("review checks missing")
    missing = [key for key in REQUIRED_CHECKS if checks.get(key) is not True]
    if missing:
        raise ValueError("public review missing true checks: " + ", ".join(missing))
    return {"sha256": actual_sha, "reviewer": data["reviewer"], "approval_scope": "PUBLIC"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("review", type=Path)
    args = parser.parse_args()
    try:
        result = validate_public_review(args.video, args.review, Path.cwd())
    except ValueError as exc:
        parser.exit(1, f"BLOCKED: {exc}\n")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
