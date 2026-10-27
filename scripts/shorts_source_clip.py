#!/usr/bin/env python3
"""Render a rights-documented 30–40s Short from a local source video.

No TTS, no voiceover, no upload, and no network access. Original audio is kept.
Caption cues must already be timed relative to the selected clip. A rights record
is required but must still be independently checked before publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

# Direct CLI invocation (python scripts/shorts_source_clip.py) sets sys.path[0]
# to scripts/, so restore the repository root for scripts.* QC imports.
if __package__ in (None, ""):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


TIME_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
CUE_RE = re.compile(r"(?m)^(\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2},\d{3})")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for piece in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(piece)
    return digest.hexdigest()


def _time(value: str) -> float:
    match = TIME_RE.fullmatch(value)
    if not match:
        raise ValueError("caption time format must be HH:MM:SS,mmm")
    hours, minutes, seconds, millis = map(int, match.groups())
    if minutes > 59 or seconds > 59:
        raise ValueError("invalid caption timestamp")
    return hours * 3600 + minutes * 60 + seconds + millis / 1000


def check_captions(path: Path, seconds: float) -> None:
    content = path.read_text(encoding="utf-8-sig")
    # Validate whole SRT blocks, not just timestamp lines: an empty cue is unsafe.
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip()
    blocks = re.split(r"\n[ \t]*\n+", normalized) if normalized else []
    cues = []
    readability = []
    for block in blocks:
        lines = block.split("\n")
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        if len(lines) < 2:
            raise ValueError("caption cue text missing; no inferred transcript")
        match = CUE_RE.fullmatch(lines[0].strip())
        if not match:
            raise ValueError("captions must contain timed SRT cues; no inferred transcript")
        text = "\n".join(lines[1:])
        if not re.sub(r"<[^>]+>", "", text).strip():
            raise ValueError("caption cue text missing; no inferred transcript")
        cues.append(match.groups())
        readability.append((match.groups(), text))
    if not cues:
        raise ValueError("captions must contain timed SRT cues; no inferred transcript")
    previous_end = 0.0
    for start_text, end_text in cues:
        start, end = _time(start_text), _time(end_text)
        if start < previous_end - 0.01 or end <= start or end > seconds + 0.10:
            raise ValueError("caption cues overlap, are invalid, or run beyond clip")
        previous_end = end
    # Conservative timeline coverage only; spoken-word sync still requires independent QA.
    max_uncovered_seconds = 3.0
    if _time(cues[0][0]) > max_uncovered_seconds:
        raise ValueError("captions do not start in first three seconds")
    previous_end = 0.0
    for start_text, end_text in cues:
        start, end = _time(start_text), _time(end_text)
        if start - previous_end > max_uncovered_seconds:
            raise ValueError("caption timeline has uncovered gap; transcript review required")
        previous_end = end
    if seconds - previous_end > max_uncovered_seconds:
        raise ValueError("caption timeline has uncovered ending; transcript review required")
    # Reading speed is a conservative screen, not a spoken-word sync verdict.
    # Never silently rewrite or stretch sourced captions; require a human review.
    for (start_text, end_text), caption_text in readability:
        visible = re.sub(r"<[^>]+>", "", caption_text)
        char_count = len(" ".join(visible.split()))
        cue_seconds = _time(end_text) - _time(start_text)
        if char_count / cue_seconds > 20.0:
            raise ValueError("caption reading speed exceeds 20 characters/second; human review required")


def validate_rights(source: Path, captions: Path, record: Path, language: str) -> dict:
    try:
        evidence = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("rights evidence JSON is missing or invalid") from exc
    if not isinstance(evidence, dict):
        raise ValueError("rights evidence must be an object")
    for key in ("source_url", "license_url", "license_name", "verified_by", "verified_at"):
        value = evidence.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"rights evidence missing {key}")
    for key in ("source_url", "license_url"):
        parsed = urlparse(evidence[key])
        if parsed.scheme != "https" or not parsed.netloc:
            raise ValueError(f"rights evidence {key} must be an HTTPS URL")
    for key in ("reuse_permitted", "derivatives_permitted", "audio_reuse_permitted"):
        if evidence.get(key) is not True:
            raise ValueError(f"rights evidence must explicitly affirm {key}")
    recorded_hash = evidence.get("source_sha256")
    if not isinstance(recorded_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", recorded_hash):
        raise ValueError("rights evidence requires source_sha256")
    if file_sha256(source) != recorded_hash:
        raise ValueError("source video hash does not match rights evidence")
    # Caption wording and timing are separately copyrighted assets. A valid
    # source-video license does not grant subtitle reuse or adaptation rights.
    for key in ("caption_license_name", "caption_license_url"):
        value = evidence.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"rights evidence missing {key}")
    caption_license = urlparse(evidence["caption_license_url"])
    if caption_license.scheme != "https" or not caption_license.netloc:
        raise ValueError("rights evidence caption_license_url must be an HTTPS URL")
    for key in ("caption_reuse_permitted", "caption_derivatives_permitted"):
        if evidence.get(key) is not True:
            raise ValueError(f"rights evidence must explicitly affirm {key}")
    caption_hash = evidence.get("caption_sha256")
    if not isinstance(caption_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", caption_hash):
        raise ValueError("rights evidence requires caption_sha256")
    if file_sha256(captions) != caption_hash:
        raise ValueError("caption hash does not match rights evidence")
    normalized = language.lower().split("-", 1)[0]
    for key in ("spoken_language", "caption_language"):
        value = evidence.get(key)
        if not isinstance(value, str) or value.lower().split("-", 1)[0] != normalized:
            raise ValueError(f"{key} must match the original spoken language")
    # A file or flag cannot prove ownership or third-party rights.
    # Publication remains blocked regardless of this intake record.
    return evidence


def _probe(path: Path) -> dict:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,duration:format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError("ffprobe could not inspect the source or output")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("ffprobe returned malformed JSON") from exc


def _duration(payload: dict) -> float:
    try:
        duration = float(payload["format"]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("video duration cannot be established") from exc
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("invalid video duration")
    return duration


def _require_audio_coverage(streams: list[dict], seconds: float) -> None:
    """Fail closed when the rendered original-audio stream is too short."""
    audio = [stream for stream in streams if stream.get("codec_type") == "audio"]
    if len(audio) != 1:
        raise RuntimeError("rendered MP4 must have exactly one original audio stream")
    try:
        audio_duration = float(audio[0]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("rendered MP4 audio duration unavailable") from exc
    if not math.isfinite(audio_duration) or audio_duration < seconds - 0.30:
        raise RuntimeError("rendered MP4 audio does not cover full clip")


def _require_video_coverage(streams: list[dict], seconds: float) -> None:
    """Fail closed when the rendered video track ends before the clip."""
    video = [stream for stream in streams if stream.get("codec_type") == "video"]
    if len(video) != 1:
        raise RuntimeError("rendered MP4 must have exactly one video stream")
    try:
        video_duration = float(video[0]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("rendered MP4 video duration unavailable") from exc
    if not math.isfinite(video_duration) or video_duration < seconds - 0.30:
        raise RuntimeError("rendered MP4 video does not cover full clip")



def _caption_margin_ass_units(width: int, height: int) -> int:
    """Place SRT captions inside the visible image, not in letterbox padding.

    FFmpeg converts SRT to ASS with PlayResY=288; force_style MarginV uses
    ASS script units, NOT output pixels. A raw 700px value would put captions
    off-screen. This is a framing default, not a substitute for scene QA.
    """
    if width <= 0 or height <= 0:
        raise ValueError("source dimensions must be positive")
    visible_height = min(1920.0, 1080.0 * height / width)
    bottom_padding_px = (1920.0 - visible_height) / 2.0
    target_bottom_margin_px = bottom_padding_px + 90.0
    return max(18, round(target_bottom_margin_px * 288.0 / 1920.0))


def render(source: Path, captions: Path, evidence_file: Path, output: Path, *, start: float, seconds: float, language: str) -> dict:
    source, captions, evidence_file, output = map(lambda x: Path(x).resolve(), (source, captions, evidence_file, output))
    if not all(path.is_file() for path in (source, captions, evidence_file)):
        raise ValueError("source, captions and rights evidence must be existing local files")
    if source == output:
        raise ValueError("cannot overwrite source video")
    if source.suffix.lower() not in {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".ogv"}:
        raise ValueError("source must be a local video file")
    if output.exists():
        raise ValueError("output already exists; refusing to overwrite")
    if captions.suffix.lower() != ".srt" or output.suffix.lower() != ".mp4":
        raise ValueError("captions must be SRT and output must be MP4")
    if not all(math.isfinite(x) for x in (start, seconds)) or start < 0 or not 30 <= seconds <= 40:
        raise ValueError("start must be nonnegative and clip duration 30–40 seconds")
    if not re.fullmatch(r"[A-Za-z]{2}(?:-[A-Za-z]{2})?", language):
        raise ValueError("language must be a BCP-47 language tag, e.g. en or tr")
    rights = validate_rights(source, captions, evidence_file, language)
    for binary in ("ffmpeg", "ffprobe"):
        if not shutil.which(binary):
            raise RuntimeError(f"missing required free binary: {binary}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="licensed-short-", dir=str(output.parent)) as tmp:
        work = Path(tmp)
        # Source paths can change between rights validation and FFmpeg opening them.
        # Render only a private snapshot whose bytes match the licensed SHA-256.
        snapshot = work / ("source" + source.suffix.lower())
        shutil.copyfile(source, snapshot)
        if file_sha256(snapshot) != rights["source_sha256"]:
            raise ValueError("source changed during rights-checked snapshot; render blocked")
        # Validate exactly the private SRT snapshot that FFmpeg will burn in.
        # A swapped caption file must never bypass timeline validation.
        captions_snapshot = work / "captions.srt"
        shutil.copyfile(captions, captions_snapshot)
        if file_sha256(captions_snapshot) != rights["caption_sha256"]:
            raise ValueError("captions changed during rights-checked snapshot")
        check_captions(captions_snapshot, seconds)
        source_info = _probe(snapshot)
        if _duration(source_info) + 0.05 < start + seconds:
            raise ValueError("requested clip extends beyond source duration")
        streams = source_info.get("streams", [])
        source_video_tracks = [s for s in streams if s.get("codec_type") == "video"]
        if (len(source_video_tracks) != 1 or not source_video_tracks[0].get("width")
                or not source_video_tracks[0].get("height")):
            raise ValueError("source must have exactly one unambiguous video track")
        # The first audio track is not necessarily the spoken-language track.
        # Never silently choose one from multiple tracks: it may contain a
        # different language, commentary or music with separate rights.
        source_audio_tracks = [s for s in streams if s.get("codec_type") == "audio"]
        if len(source_audio_tracks) != 1:
            raise ValueError("source must have exactly one unambiguous original audio track")
        candidate = work / "candidate.mp4"
        # Pad rather than crop: preserves people and objects when center-crop would cut them off.
        caption_margin = _caption_margin_ass_units(
            int(source_video_tracks[0]["width"]), int(source_video_tracks[0]["height"])
        )
        filt = ("scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30,"
                "format=yuv420p,subtitles=captions.srt:"
                f"force_style='Alignment=2,MarginV={caption_margin}'")
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-n",
                   "-ss", f"{start:.3f}", "-i", str(snapshot), "-t", f"{seconds:.3f}",
                   "-map", "0:v:0", "-map", "0:a:0", "-vf", filt,
                   "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
                   "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", str(candidate)]
        proc = subprocess.run(command, cwd=str(work), capture_output=True, text=True, timeout=300, check=False)
        if proc.returncode != 0:
            raise RuntimeError("FFmpeg render failed: " + proc.stderr[-600:])
        if not candidate.is_file():
            raise RuntimeError("render did not produce MP4")
        info = _probe(candidate)
        actual = _duration(info)
        if abs(actual - seconds) > 0.3:
            raise RuntimeError(f"clip duration differs from requested duration: {actual:.2f}s")
        streams = info.get("streams", [])
        if not any(s.get("codec_type") == "video" and s.get("width") == 1080 and s.get("height") == 1920 for s in streams):
            raise RuntimeError("rendered MP4 is not portrait 1080x1920")
        _require_video_coverage(streams, seconds)
        _require_audio_coverage(streams, seconds)
        from scripts.shorts_motion_qc import inspect as inspect_motion
        motion = inspect_motion(candidate)
        if motion.get("motion_qc") != "PASS_TECHNICAL_ONLY":
            raise RuntimeError("motion QC_BLOCKED; final MP4 not created")
        from scripts.shorts_audio_qc import inspect as inspect_audio
        audio = inspect_audio(candidate)
        if audio.get("audio_qc") != "PASS_TECHNICAL_ONLY":
            raise RuntimeError("audio QC_BLOCKED; final MP4 not created")
        # The earlier exists() check is not atomic: another process could create
        # the destination while FFmpeg/QC is running. Both files are on the same
        # filesystem, so link() atomically fails instead of clobbering it.
        try:
            os.link(candidate, output)
        except FileExistsError as exc:
            raise ValueError("output appeared during render; refusing to overwrite") from exc
        return {"output": str(output), "output_sha256": file_sha256(output),
                "source_sha256": file_sha256(snapshot), "duration": actual,
                "spoken_language": language, "caption_language": language,
                "audio_source": "original_source", "synthetic_narration": False,
                "motion_qc": motion["motion_qc"], "audio_qc": audio["audio_qc"],
                "publish_ready": False, "rights_review_pending": True,
                "independent_media_review_pending": True, "credits_spent": 0}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "captions", "evidence", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--start", type=float, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--language", type=str, required=True)
    args = parser.parse_args()
    try:
        report = render(args.source, args.captions, args.evidence, args.output,
                        start=args.start, seconds=args.duration, language=args.language)
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"ok": True, **report}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
