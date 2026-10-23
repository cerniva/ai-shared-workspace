#!/usr/bin/env python3
"""Conservative FFmpeg freeze screen for a 30–40s sourced Short.

A pass is technical motion evidence only; it is never publication approval.
Source rights, third-party audio, timed transcript and independent QA remain
separate fail-closed gates. Free local ffmpeg/ffprobe only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

FREEZE_START = re.compile(r"freeze_start:\s*([0-9.]+)")
FREEZE_END = re.compile(r"freeze_end:\s*([0-9.]+)")


def inspect(path: Path, *, max_freeze: float = 3.0, max_ratio: float = 0.20) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError("input MP4 not found")
    p = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "json", str(path)],
        capture_output=True, text=True, timeout=30,
    )
    if p.returncode:
        raise RuntimeError("ffprobe failed")
    duration = float(json.loads(p.stdout)["format"]["duration"])
    if not 29.7 <= duration <= 40.3:
        raise ValueError("duration outside expected 30-40s range")
    run = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-map", "0:v:0", "-vf", "freezedetect=n=-45dB:d=3",
         "-an", "-f", "null", "-"],
        capture_output=True, text=True, timeout=120,
    )
    if run.returncode:
        raise RuntimeError("full-duration FFmpeg decode/freezedetect failed")
    starts = []
    intervals = []
    for line in run.stderr.splitlines():
        a = FREEZE_START.search(line)
        b = FREEZE_END.search(line)
        if a:
            starts.append(float(a.group(1)))
        if b and starts:
            intervals.append((starts.pop(0), float(b.group(1))))
    # ffmpeg can omit freeze_end if the last frames stay frozen through EOF.
    for s in starts:
        intervals.append((s, duration))
    frozen = sum(max(0, min(duration, e) - s) for s, e in intervals)
    longest = max([max(0, e - s) for s, e in intervals] or [0])
    blocked = longest >= max_freeze or frozen / duration >= max_ratio
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return {
        "media_sha256": h.hexdigest(),
        "duration_seconds": round(duration, 3),
        "freeze_intervals": [[round(s, 3), round(e, 3)] for s, e in intervals],
        "longest_freeze_seconds": round(longest, 3),
        "frozen_fraction": round(frozen / duration, 4),
        "motion_qc": "QC_BLOCKED" if blocked else "PASS_TECHNICAL_ONLY",
        "publish_ready": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        result = inspect(args.input)
        print(json.dumps(result, ensure_ascii=False))
        raise SystemExit(2 if result["motion_qc"] == "QC_BLOCKED" else 0)
    except Exception as exc:
        print(json.dumps({
            "motion_qc": "QC_BLOCKED", "error": str(exc),
            "publish_ready": False,
        }))
        raise SystemExit(2)
