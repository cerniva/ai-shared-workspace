#!/usr/bin/env python3
"""Credit-free Shorts renderer using local FFmpeg only.

It assembles existing local images/video, narration, optional music and optional
SRT subtitles into a 1080x1920 H.264/AAC MP4. It does not call external media
APIs, upload anything, or spend generation credits.

Usage:
  python3 scripts/shorts_render.py render.json output.mp4

Manifest paths are resolved relative to the manifest file. Example:
{
  "target_seconds": 30,
  "visuals": [
    {"path": "assets/one.jpg", "duration": 4},
    {"path": "assets/two.mp4", "duration": 6}
  ],
  "narration": "audio/voice.wav",
  "music": "audio/music.mp3",
  "music_volume": 0.10,
  "subtitles": "captions.srt"
}
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".ppm"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
VIDEO_FILTER = (
    "scale=1080:1920:force_original_aspect_ratio=increase,"
    "crop=1080:1920,setsar=1,fps=30,format=yuv420p"
)


def _resolve(base: Path, value: str, field: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty path")
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    if not path.is_file():
        raise ValueError(f"{field} does not exist: {path}")
    return path


def validate_spec(spec: dict, base_dir: Path) -> dict:
    """Validate and normalize a render manifest without invoking FFmpeg."""
    if not isinstance(spec, dict):
        raise ValueError("render spec must be a JSON object")

    visuals = spec.get("visuals")
    if not isinstance(visuals, list) or not visuals:
        raise ValueError("visuals must contain at least one visual")

    normalized_visuals = []
    total_visual_seconds = 0.0
    for index, item in enumerate(visuals):
        if not isinstance(item, dict):
            raise ValueError(f"visuals[{index}] must be an object")
        path = _resolve(base_dir, item.get("path"), f"visuals[{index}].path")
        try:
            duration = float(item.get("duration"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"visuals[{index}].duration must be a number") from exc
        if duration <= 0 or duration > 180:
            raise ValueError(f"visuals[{index}].duration must be between 0 and 180 seconds")
        suffix = path.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            kind = "image"
        elif suffix in VIDEO_EXTENSIONS:
            kind = "video"
        else:
            raise ValueError(f"unsupported visual type: {path.name}")
        normalized_visuals.append({"path": path, "duration": duration, "kind": kind})
        total_visual_seconds += duration

    narration = _resolve(base_dir, spec.get("narration"), "narration")
    music = _resolve(base_dir, spec["music"], "music") if spec.get("music") else None
    subtitles = _resolve(base_dir, spec["subtitles"], "subtitles") if spec.get("subtitles") else None
    if subtitles and subtitles.suffix.lower() != ".srt":
        raise ValueError("subtitles must be an .srt file")

    try:
        target_seconds = float(spec.get("target_seconds", total_visual_seconds))
    except (TypeError, ValueError) as exc:
        raise ValueError("target_seconds must be a number") from exc
    if target_seconds <= 0 or target_seconds > 180:
        raise ValueError("target_seconds must be between 0 and 180 seconds")
    if target_seconds > total_visual_seconds + 0.001:
        raise ValueError("target_seconds cannot exceed the total visual duration")

    try:
        music_volume = float(spec.get("music_volume", 0.10))
    except (TypeError, ValueError) as exc:
        raise ValueError("music_volume must be a number") from exc
    if not 0 <= music_volume <= 1:
        raise ValueError("music_volume must be between 0 and 1")

    return {
        "visuals": normalized_visuals,
        "narration": narration,
        "music": music,
        "subtitles": subtitles,
        "music_volume": music_volume,
        "target_seconds": target_seconds,
    }


def _run(args: list[str], *, cwd: Path | None = None) -> None:
    try:
        subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "ffmpeg failed")[-4000:]
        raise RuntimeError(detail) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("ffmpeg timed out") from exc


def _require_tools() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if not shutil.which(name)]
    if missing:
        raise RuntimeError("Missing required tools: " + ", ".join(missing))


def _render_segment(item: dict, output: Path) -> None:
    path = item["path"]
    duration = item["duration"]
    if item["kind"] == "image":
        inputs = ["-loop", "1", "-framerate", "30", "-i", str(path)]
    else:
        inputs = ["-stream_loop", "-1", "-i", str(path)]
    _run([
        "ffmpeg", "-y", *inputs,
        "-t", f"{duration:.3f}",
        "-an",
        "-vf", VIDEO_FILTER,
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "21",
        "-pix_fmt", "yuv420p",
        str(output),
    ])


def render(manifest_path: Path, output_path: Path) -> dict:
    """Render one Shorts manifest and return deterministic output metadata."""
    _require_tools()
    manifest_path = Path(manifest_path).resolve()
    output_path = Path(output_path).resolve()
    if not manifest_path.is_file():
        raise ValueError(f"manifest does not exist: {manifest_path}")
    try:
        spec = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("manifest is not valid JSON") from exc
    normalized = validate_spec(spec, manifest_path.parent)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="shorts-render-") as temp_name:
        temp = Path(temp_name)
        segments = []
        for index, visual in enumerate(normalized["visuals"]):
            segment = temp / f"segment-{index:03d}.mp4"
            _render_segment(visual, segment)
            segments.append(segment)

        concat_file = temp / "segments.txt"
        concat_file.write_text(
            "".join(f"file '{segment.as_posix()}'\n" for segment in segments),
            encoding="utf-8",
        )
        visual_track = temp / "visual.mp4"
        _run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
            "-c", "copy", str(visual_track),
        ])

        command = [
            "ffmpeg", "-y",
            "-i", str(visual_track),
            "-i", str(normalized["narration"]),
        ]
        if normalized["music"]:
            command.extend(["-stream_loop", "-1", "-i", str(normalized["music"])])

        if normalized["subtitles"]:
            subtitle_copy = temp / "captions.srt"
            shutil.copyfile(normalized["subtitles"], subtitle_copy)
            command.extend(["-vf", "subtitles=captions.srt"])

        if normalized["music"]:
            volume = normalized["music_volume"]
            command.extend([
                "-filter_complex",
                f"[1:a:0]volume=1.0[voice];[2:a:0]volume={volume:.4f}[music];"
                "[voice][music]amix=inputs=2:duration=longest:dropout_transition=2[aout]",
                "-map", "0:v:0", "-map", "[aout]",
            ])
        else:
            command.extend(["-map", "0:v:0", "-map", "1:a:0"])

        command.extend([
            "-t", f"{normalized['target_seconds']:.3f}",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "21",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "160k",
            "-movflags", "+faststart",
            str(output_path),
        ])
        _run(command, cwd=temp)

    if not output_path.is_file() or output_path.stat().st_size == 0:
        raise RuntimeError("renderer produced no output")
    return {
        "output": str(output_path),
        "target_seconds": normalized["target_seconds"],
        "visual_count": len(normalized["visuals"]),
        "credits_spent": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        result = render(args.manifest, args.output)
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
