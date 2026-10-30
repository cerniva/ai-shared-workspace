#!/usr/bin/env python3
"""Validate an ordered multi-cut plan and build a test-only FFmpeg concat graph.

This is a technical preflight helper, NOT a licensed-source renderer, rights
approval, transcript synchronizer, or publication gate. The production renderer
must separately bind source/SRT SHA, enforce rights, and perform full media QA.
"""
from __future__ import annotations

import math


def validate_segments(segments, source_duration, *, enforce_shorts=True):
    """Return total duration; reject invalid source-cut ordering and coverage."""
    if not isinstance(segments, (list, tuple)) or not 1 <= len(segments) <= 8:
        raise ValueError("expected 1–8 ordered source segments")
    if not isinstance(source_duration, (int, float)) or not math.isfinite(source_duration) or source_duration <= 0:
        raise ValueError("source duration must be positive and finite")
    total = 0.0
    previous_end = 0.0
    for i, segment in enumerate(segments):
        if not isinstance(segment, (list, tuple)) or len(segment) != 2:
            raise ValueError("each segment must be [start, end]")
        start, end = segment
        if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in (start, end)):
            raise ValueError("segment timestamps must be finite numbers")
        if start < 0 or end <= start or (i and start < previous_end):
            raise ValueError("segments must be ordered, non-overlapping and positive")
        if end > source_duration + 0.001:
            raise ValueError("segment extends beyond source duration")
        total += end - start
        previous_end = end
    if enforce_shorts and not 30 <= total <= 40:
        raise ValueError("selected total must be 30–40 seconds")
    return round(total, 3)


def build_concat_graph(segments, source_duration, *, enforce_shorts=True):
    """FFmpeg trim/atrim + setpts/asetpts + concat preserving selected source audio.

    Labels [vcat]/[acat] must be mapped by a caller. This graph never adds TTS,
    does not select between ambiguous source audio streams and does not burn SRT.
    It is not a replacement for scripts/shorts_source_clip.py's rights gates.
    """
    validate_segments(segments, source_duration, enforce_shorts=enforce_shorts)
    chains = []
    inputs = []
    for i, (start, end) in enumerate(segments):
        s, e = f"{start:.3f}", f"{end:.3f}"
        chains.append(f"[0:v:0]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{i}]")
        chains.append(f"[0:a:0]atrim=start={s}:end={e},asetpts=PTS-STARTPTS[a{i}]")
        inputs.append(f"[v{i}][a{i}]")
    chains.append("".join(inputs) + f"concat=n={len(segments)}:v=1:a=1[vcat][acat]")
    return ";".join(chains)
