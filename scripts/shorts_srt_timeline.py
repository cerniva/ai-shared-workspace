#!/usr/bin/env python3
"""Audit source SRT cue boundaries for a multi-segment Short, without rendering.

Never rewrite subtitle text, generate word timing, clear rights, or label an
output publish-ready. Only map existing cues to the proposed edit timeline.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

STAMP = re.compile(r"^(\d{2}):(\d{2}):(\d{2})(?:[,.](\d{3}))?$")
ARROW = re.compile(r"^(.+?)\s+-->\s+(.+?)$")


def parse_stamp(value: str) -> float:
    m = STAMP.fullmatch(value.strip())
    if not m:
        raise ValueError("invalid SRT timestamp")
    h, minute, second = map(int, m.group(1, 2, 3))
    if minute > 59 or second > 59:
        raise ValueError("invalid SRT timestamp")
    return h * 3600 + minute * 60 + second + int(m.group(4) or 0) / 1000


def read_cues(text: str) -> list[dict]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff").strip()
    if not normalized:
        raise ValueError("empty transcript")
    result = []
    prev_end = 0.0
    for idx, block in enumerate(re.split(r"\n[ \t]*\n+", normalized), 1):
        lines = block.split("\n")
        if lines[0].strip().isdigit():
            lines = lines[1:]
        if len(lines) < 2 or not " ".join(lines[1:]).strip():
            raise ValueError(f"missing cue text in block {idx}")
        m = ARROW.fullmatch(lines[0].strip())
        if not m:
            raise ValueError(f"invalid cue timing in block {idx}")
        start, end = parse_stamp(m.group(1)), parse_stamp(m.group(2))
        if end <= start or start < prev_end - 0.001:
            raise ValueError(f"overlapping or invalid cue {idx}")
        result.append({"cue": idx, "start": start, "end": end,
                       "max_line_chars": max(len(line.strip()) for line in lines[1:]),
                       "line_count": sum(bool(line.strip()) for line in lines[1:])})
        prev_end = end
    return result


def audit(srt: Path, expected_sha256: str, segments: list[tuple[float, float]]) -> dict:
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("expected SHA-256 must be 64 lowercase hex characters")
    actual = hashlib.sha256(srt.read_bytes()).hexdigest()
    if actual != expected_sha256:
        raise ValueError("source SRT SHA-256 mismatch")
    if not segments or any(not all(math.isfinite(x) for x in segment) or segment[0] < 0 or segment[1] <= segment[0] for segment in segments):
        raise ValueError("invalid edit segments")
    if any(segments[i][1] > segments[i + 1][0] for i in range(len(segments) - 1)):
        raise ValueError("source segments must be ordered and non-overlapping")
    total = sum(end - start for start, end in segments)
    if not 30 <= total <= 40:
        raise ValueError("Short must be 30-40 seconds")
    cues = read_cues(srt.read_text(encoding="utf-8-sig"))
    mapped, crossed = [], []
    offset = 0.0
    for start, end in segments:
        for cue in cues:
            if cue["end"] <= start or cue["start"] >= end:
                continue
            if cue["start"] < start - 0.001 or cue["end"] > end + 0.001:
                crossed.append(cue["cue"])
                continue
            mapped.append({"cue": cue["cue"], "source_start": cue["start"],
                           "source_end": cue["end"],
                           "short_start": round(offset + cue["start"] - start, 3),
                           "short_end": round(offset + cue["end"] - start, 3),
                           "max_line_chars": cue["max_line_chars"],
                           "line_count": cue["line_count"]})
        offset += end - start
    if not mapped:
        raise ValueError("no fully contained transcript cues")
    overlong = [c["cue"] for c in mapped if c["max_line_chars"] > 42 or c["line_count"] > 2]
    format_conversion_required = any("," not in line and "." not in line
        for line in srt.read_text(encoding="utf-8-sig").splitlines() if "-->" in line)
    technical_blockers = (
        (["BOUNDARY_CROSSING_CUE"] if crossed else [])
        + (["SRT_MILLISECONDS_REQUIRED"] if format_conversion_required else [])
        + (["MOBILE_READABILITY_REVIEW"] if overlong else [])
    )
    return {"source_srt_sha256": actual, "duration": round(total, 3),
            "segments": segments, "mapped_cues": mapped,
            "boundary_crossing_cues": sorted(set(crossed)),
            "mobile_readability_review_cues": overlong,
            "timeline_boundary_gate": "BLOCKED" if crossed else "PASS_TECHNICAL_ONLY",
            "caption_format_conversion_required": format_conversion_required,
            "technical_preflight_gate": "BLOCKED" if technical_blockers else "PASS_TECHNICAL_ONLY",
            "technical_preflight_blockers": technical_blockers,
            "rights_review_pending": True, "speech_sync_review_pending": True,
            "framing_review_pending": True, "publish_ready": False}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--srt", type=Path, required=True)
    p.add_argument("--expected-sha256", required=True)
    p.add_argument("--segment", action="append", required=True, help="start:end source seconds")
    args = p.parse_args()
    try:
        parts = [tuple(float(x) for x in item.split(":")) for item in args.segment]
        if any(len(item) != 2 for item in parts):
            raise ValueError("each segment must have start:end")
        report = audit(args.srt, args.expected_sha256, parts)
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2
    print(json.dumps({"ok": report["technical_preflight_gate"] == "PASS_TECHNICAL_ONLY", **report}))
    return 0 if report["technical_preflight_gate"] == "PASS_TECHNICAL_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
