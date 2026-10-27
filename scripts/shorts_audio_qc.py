#!/usr/bin/env python3
"""Fail-closed original-audio activity check; never publication approval."""
from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path

START = re.compile(r"silence_start:\s*([0-9.]+)")
END = re.compile(r"silence_end:\s*([0-9.]+)")


def inspect(path: Path, *, max_silence: float = 6.0, max_fraction: float = 0.45) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError("input MP4 not found")
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
         "stream=codec_type,duration:format=duration", "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    if probe.returncode:
        raise RuntimeError("ffprobe failed for audio")
    payload = json.loads(probe.stdout)
    duration = float(payload["format"]["duration"])
    if not math.isfinite(duration) or not 29.7 <= duration <= 40.3:
        raise ValueError("duration outside 30-40 seconds")
    streams = [s for s in payload.get("streams", []) if s.get("codec_type") == "audio"]
    if len(streams) != 1:
        raise RuntimeError("expected exactly one original audio stream")
    try:
        audio_duration = float(streams[0]["duration"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("audio stream duration unavailable") from exc
    if not math.isfinite(audio_duration) or audio_duration < duration - 0.30:
        raise RuntimeError("audio stream does not cover full clip")
    run = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-map", "0:a:0",
         "-af", "silencedetect=noise=-42dB:d=1.2", "-vn", "-f", "null", "-"],
        capture_output=True, text=True, timeout=120,
    )
    if run.returncode:
        raise RuntimeError("full-duration audio decode/silencedetect failed")
    starts = []
    intervals = []
    for line in run.stderr.splitlines():
        a = START.search(line)
        b = END.search(line)
        if a:
            starts.append(float(a.group(1)))
        if b and starts:
            intervals.append((starts.pop(0), float(b.group(1))))
    for start in starts:
        intervals.append((start, duration))
    intervals = [(max(0.0, s), min(duration, e)) for s, e in intervals if e > s]
    silence = sum(e - s for s, e in intervals)
    longest = max((e - s for s, e in intervals), default=0.0)
    fraction = silence / duration
    blocked = longest >= max_silence or fraction >= max_fraction
    return {
        "duration_seconds": round(duration, 3),
        "audio_stream_duration_seconds": round(audio_duration, 3),
        "silence_intervals": [[round(s, 3), round(e, 3)] for s, e in intervals],
        "longest_silence_seconds": round(longest, 3),
        "silence_fraction": round(fraction, 4),
        "audio_qc": "QC_BLOCKED" if blocked else "PASS_TECHNICAL_ONLY",
        "publish_ready": False,
    }
