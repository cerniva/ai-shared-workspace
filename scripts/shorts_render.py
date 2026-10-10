#!/usr/bin/env python3
"""Credit-free Shorts renderer using local FFmpeg and optional offline eSpeak NG.

It assembles existing local images/video, narration, optional music and optional
SRT subtitles into a 1080x1920 H.264/AAC MP4. Narration can come from an
existing audio file or be synthesized from text. The default TTS is offline eSpeak
NG; "narration_engine": "edge-tts" (or env SHORTS_TTS_ENGINE=edge-tts) opts into the
free, keyless edge-tts neural voices (tr-TR-AhmetNeural) and falls back to eSpeak
on any failure. It never uploads anything or spends generation credits.

Usage:
  python3 scripts/shorts_render.py render.json output.mp4

Manifest paths are resolved relative to the manifest file. Existing-audio example:
{
  "target_seconds": 30,
  "visuals": [
    {"path": "assets/one.jpg", "duration": 4},
    {"path": "assets/two.mp4", "duration": 26}
  ],
  "narration": "audio/voice.wav",
  "music": "audio/music.mp3",
  "music_volume": 0.10,
  "subtitles": "captions.srt"
}

Zero-credit text narration example:
{
  "target_seconds": 30,
  "visuals": [{"path": "assets/one.jpg", "duration": 30}],
  "narration_text": "Your narration text here.",
  "narration_voice": "en-us",
  "narration_speed": 165
}
"""

from __future__ import annotations

import argparse
import json
import os
import re
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
VOICE_RE = re.compile(r"^[A-Za-z0-9_.+\-]{1,64}$")
# "edge-tts" is a free, keyless neural voice (e.g. tr-TR-AhmetNeural); it needs
# network access, so the renderer falls back to offline eSpeak NG on any failure.
TTS_ENGINES = {"espeak", "edge-tts"}
ESPEAK_SPEED_BASELINE = 165
END_PAD_SECONDS = 0.6
NEURAL_VOICES = {"tr": "tr-TR-AhmetNeural", "en-us": "en-US-GuyNeural", "en": "en-US-GuyNeural"}


def _resolve(base: Path, value: str, field: str) -> Path:
    """Resolve a required manifest path relative to the manifest directory."""
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
    """Validate and normalize a render manifest without invoking external tools."""
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

    narration_value = spec.get("narration")
    narration_text = spec.get("narration_text")
    if narration_value and narration_text:
        raise ValueError("use either narration or narration_text, not both")
    if narration_value:
        narration = _resolve(base_dir, narration_value, "narration")
        narration_text = None
    else:
        narration = None
        if not isinstance(narration_text, str) or not narration_text.strip():
            raise ValueError("narration or narration_text is required")
        narration_text = narration_text.strip()
        if len(narration_text) > 5000:
            raise ValueError("narration_text must be 5000 characters or fewer")

    narration_voice = spec.get("narration_voice", "en-us")
    if not isinstance(narration_voice, str) or not VOICE_RE.fullmatch(narration_voice):
        raise ValueError("narration_voice contains unsupported characters")
    fallback_voice = spec.get("narration_fallback_voice")
    narration_engine = spec.get("narration_engine")
    if narration_engine is None:
        narration_engine = "espeak"
        env_engine = os.environ.get("SHORTS_TTS_ENGINE", "").strip()
        if env_engine == "edge-tts" and narration_voice.lower() in NEURAL_VOICES:
            fallback_voice = fallback_voice or narration_voice
            narration_voice = NEURAL_VOICES[narration_voice.lower()]
            narration_engine = "edge-tts"
    if narration_engine not in TTS_ENGINES:
        raise ValueError("narration_engine must be one of: " + ", ".join(sorted(TTS_ENGINES)))
    if fallback_voice is not None and (
        not isinstance(fallback_voice, str) or not VOICE_RE.fullmatch(fallback_voice)
    ):
        raise ValueError("narration_fallback_voice contains unsupported characters")
    try:
        narration_speed = int(spec.get("narration_speed", 165))
    except (TypeError, ValueError) as exc:
        raise ValueError("narration_speed must be an integer") from exc
    if not 80 <= narration_speed <= 450:
        raise ValueError("narration_speed must be between 80 and 450")

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
        "narration_text": narration_text,
        "narration_voice": narration_voice,
        "narration_engine": narration_engine,
        "narration_fallback_voice": fallback_voice,
        "narration_speed": narration_speed,
        "music": music,
        "subtitles": subtitles,
        "music_volume": music_volume,
        "target_seconds": target_seconds,
    }


def _run(args: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    """Run a media command with bounded execution time and readable failures."""
    try:
        return subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "command failed")[-4000:]
        raise RuntimeError(detail) from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError("media command timed out") from exc


def _require_tools(*, require_tts: bool = False) -> None:
    """Fail before rendering when required local binaries are unavailable."""
    names = ["ffmpeg", "ffprobe"]
    if require_tts:
        names.append("espeak-ng")
    missing = [name for name in names if not shutil.which(name)]
    if missing:
        raise RuntimeError("Missing required tools: " + ", ".join(missing))


def _render_segment(item: dict, output: Path) -> None:
    """Normalize one image or video visual into a portrait H.264 segment."""
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


def _synthesize_narration(text: str, voice: str, speed: int, output: Path) -> None:
    """Synthesize narration locally with eSpeak NG and verify audio was created."""
    _run([
        "espeak-ng",
        "-v", voice,
        "-s", str(speed),
        "-w", str(output),
        "--",
        text,
    ])
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("offline narration produced no audio")


def _edge_rate(speed: int) -> str:
    """Map an eSpeak words-per-minute speed onto an edge-tts percentage rate."""
    pct = round((speed - ESPEAK_SPEED_BASELINE) * 100 / ESPEAK_SPEED_BASELINE)
    pct = max(-50, min(100, pct))
    return f"{pct:+d}%"


def _edge_word_boundaries(text: str, voice: str, rate: str, mp3: Path) -> list[dict]:
    """Stream edge-tts audio to ``mp3`` and return WordBoundary timings in seconds."""
    try:
        import asyncio
        import edge_tts  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError("edge-tts is not installed") from exc

    async def _stream() -> list[dict]:
        words: list[dict] = []
        communicate = edge_tts.Communicate(text, voice, rate=rate, boundary="WordBoundary")
        with mp3.open("wb") as handle:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    handle.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    start = chunk["offset"] / 10_000_000
                    words.append({
                        "text": chunk["text"],
                        "start": start,
                        "end": start + chunk["duration"] / 10_000_000,
                    })
        return words

    try:
        return asyncio.run(asyncio.wait_for(_stream(), timeout=120))
    except Exception as exc:  # network/service errors -> caller falls back to eSpeak
        raise RuntimeError(f"edge-tts synthesis failed: {exc}") from exc


def _synthesize_edge(text: str, voice: str, speed: int, output: Path) -> list[dict]:
    """Synthesize narration with free, keyless edge-tts into WAV; return word timings."""
    mp3 = output.with_suffix(".edge.mp3")
    words = _edge_word_boundaries(text, voice, _edge_rate(speed), mp3)
    if not mp3.is_file() or mp3.stat().st_size == 0:
        raise RuntimeError("edge-tts produced no audio")
    _run(["ffmpeg", "-y", "-i", str(mp3), "-ac", "1", "-ar", "24000", str(output)])
    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("edge-tts audio conversion produced no audio")
    return words


def _srt_ts(seconds: float) -> str:
    """Format seconds as an SRT timestamp."""
    millis = max(0, int(round(seconds * 1000)))
    h, rem = divmod(millis, 3_600_000)
    m, rem = divmod(rem, 60_000)
    sec, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{sec:02d},{ms:03d}"


def srt_from_word_boundaries(text: str, words: list[dict], *, max_chars: int = 42,
                             tail: float = 0.4) -> str:
    """Build SRT cues from real TTS word timings (punctuation restored from ``text``)."""
    if not words:
        raise ValueError("no word boundaries")
    tokens = text.split()
    labels = tokens if len(tokens) == len(words) else [w["text"] for w in words]
    cues: list[list[int]] = []
    current: list[int] = []
    for index, label in enumerate(labels):
        candidate = " ".join(labels[i] for i in current + [index])
        if current and len(candidate) > max_chars:
            cues.append(current)
            current = []
        current.append(index)
        if label.endswith((".", "?", "!")):
            cues.append(current)
            current = []
    if current:
        cues.append(current)
    lines = []
    for number, cue in enumerate(cues, start=1):
        start = words[cue[0]]["start"]
        end = words[cue[-1]]["end"] + tail
        if number < len(cues):
            end = min(end, words[cues[number][0]]["start"])
        end = max(end, start + 0.3)
        lines.append(f"{number}\n{_srt_ts(start)} --> {_srt_ts(end)}\n"
                     + " ".join(labels[i] for i in cue) + "\n")
    return "\n".join(lines)


def synthesize_with_fallback(normalized: dict, output: Path) -> dict:
    """Synthesize narration with the requested engine, falling back to eSpeak NG.

    Returns which engine/voice actually produced the audio so the result is auditable.
    """
    text = normalized["narration_text"]
    speed = normalized["narration_speed"]
    engine = normalized.get("narration_engine", "espeak")
    errors: list[str] = []
    if engine == "edge-tts":
        try:
            words = _synthesize_edge(text, normalized["narration_voice"], speed, output)
            return {"engine": "edge-tts", "voice": normalized["narration_voice"],
                    "fallback_errors": [], "words": words}
        except (OSError, RuntimeError) as exc:
            errors.append(f"edge-tts: {str(exc)[-300:]}")
        voice = normalized.get("narration_fallback_voice") or "en-us"
    else:
        voice = normalized["narration_voice"]
    if not shutil.which("espeak-ng"):
        raise RuntimeError("Missing required tools: espeak-ng; " + "; ".join(errors))
    _synthesize_narration(text, voice, speed, output)
    return {"engine": "espeak", "voice": voice, "fallback_errors": errors, "words": []}


def _probe_duration(path: Path) -> float:
    """Return media duration in seconds using ffprobe."""
    result = _run([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError(f"could not determine media duration: {path}") from exc
    if duration <= 0:
        raise RuntimeError(f"invalid media duration: {path}")
    return duration


def render(manifest_path: Path, output_path: Path) -> dict:
    """Render one Shorts manifest and return deterministic output metadata."""
    manifest_path = Path(manifest_path).resolve()
    output_path = Path(output_path).resolve()
    if not manifest_path.is_file():
        raise ValueError(f"manifest does not exist: {manifest_path}")
    try:
        spec = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("manifest is not valid JSON") from exc
    normalized = validate_spec(spec, manifest_path.parent)
    _require_tools(
        require_tts=bool(normalized["narration_text"])
        and normalized["narration_engine"] == "espeak"
    )
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

        narration_track = normalized["narration"]
        narration_source = "file"
        tts_info = None
        output_seconds = normalized["target_seconds"]
        subtitle_source = "manifest" if normalized["subtitles"] else None
        if normalized["narration_text"]:
            narration_track = temp / "narration.wav"
            tts_info = synthesize_with_fallback(normalized, narration_track)
            narration_seconds = _probe_duration(narration_track)
            if narration_seconds > normalized["target_seconds"] + 0.05:
                raise ValueError(
                    "synthesized narration does not fit target_seconds: "
                    f"{narration_seconds:.2f}s > {normalized['target_seconds']:.2f}s"
                )
            narration_source = "offline_tts" if tts_info["engine"] == "espeak" else "neural_tts"
            # Cut the video to the voice so the Short never ends on dead air.
            output_seconds = min(output_seconds, narration_seconds + END_PAD_SECONDS)

        command = [
            "ffmpeg", "-y",
            "-i", str(visual_track),
            "-i", str(narration_track),
        ]
        if normalized["music"]:
            command.extend(["-stream_loop", "-1", "-i", str(normalized["music"])])

        if normalized["subtitles"]:
            subtitle_copy = temp / "captions.srt"
            if tts_info and tts_info.get("words"):
                # Real TTS word timings replace evenly-spread manifest cues.
                srt = srt_from_word_boundaries(normalized["narration_text"], tts_info["words"])
                subtitle_copy.write_text(srt, encoding="utf-8")
                normalized["subtitles"].write_text(srt, encoding="utf-8")
                subtitle_source = "tts_word_boundary"
            else:
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
            "-t", f"{output_seconds:.3f}",
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
        "output_seconds": round(output_seconds, 3),
        "subtitle_source": subtitle_source,
        "visual_count": len(normalized["visuals"]),
        "narration_source": narration_source,
        "tts": (
            {k: v for k, v in tts_info.items() if k != "words"} | {"word_count": len(tts_info["words"])}
            if tts_info else None
        ),
        "credits_spent": 0,
    }


def main() -> int:
    """Parse CLI arguments, render one manifest, and return a shell exit code."""
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
