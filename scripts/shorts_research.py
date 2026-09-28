#!/usr/bin/env python3
"""CORE-03 research gate. Does not render, upload, or spend video credits.

Usage:
  python3 scripts/shorts_research.py score --input knowledge/shorts/candidates.json
  python3 scripts/shorts_research.py check-duplicate --title "..." --hook "..."
  python3 scripts/shorts_research.py gate --packet knowledge/shorts/packets/PACKET.json

Exit 0 = research packet ready for script/visual/audio planning.
Exit 2 = blocked (do not call HyperFrames / upload).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHORTS = ROOT / "knowledge" / "shorts"
CRITERIA = [
    "hook_power",
    "curiosity",
    "first_3s",
    "watch_time",
    "completion",
    "shareability",
    "comments",
    "freshness",
    "visual",
    "reliability",
    "not_overused",
    "international",
    "channel_fit",
]
OPTIONAL_CRITERIA = [
    "monetization",
    "engagement",
    "low_production_cost",
    "rights_safety",
    "language_fit",
]
OPTIONAL_NEUTRAL_SCORE = 5.0


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _bounded_score(raw, *, default: float) -> float:
    """Convert one score to a bounded 0-10 value with an explicit fallback."""
    try:
        value = float(raw)
    except (TypeError, ValueError):
        value = default
    return max(0.0, min(10.0, value))


def score_item(item: dict) -> dict:
    """Score a candidate while keeping new optional dimensions neutral for legacy data."""
    scores = item.get("scores") or {}
    missing = [k for k in CRITERIA if k not in scores]
    required_values = [_bounded_score(scores.get(key, 0), default=0.0) for key in CRITERIA]
    optional_values = [
        _bounded_score(scores.get(key, OPTIONAL_NEUTRAL_SCORE), default=OPTIONAL_NEUTRAL_SCORE)
        for key in OPTIONAL_CRITERIA
    ]
    total = sum(required_values) + sum(optional_values)
    reliability = _bounded_score(scores.get("reliability", 0), default=0.0)
    overused = _bounded_score(scores.get("not_overused", 10), default=0.0)
    veto = reliability < 6 or overused < 4 or not item.get("unique_angle")
    return {
        **item,
        "total": round(total, 2),
        "missing_criteria": missing,
        "veto": veto,
    }


def rank(candidates: list[dict]) -> list[dict]:
    ranked = sorted((score_item(c) for c in candidates), key=lambda x: x["total"], reverse=True)
    eligible = [c for c in ranked if not c["veto"]]
    return eligible or ranked


def history_texts() -> list[str]:
    log = SHORTS / "decision-log.md"
    if not log.exists():
        return []
    return [normalize(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_duplicate(title: str, hook: str) -> bool:
    blob = "\n".join(history_texts())
    t, h = normalize(title), normalize(hook)
    if not t and not h:
        return False
    return (t and t in blob) or (h and h in blob)


def _valid_media_queries(value) -> bool:
    """Return true only for a non-empty list containing non-empty string queries."""
    return (
        isinstance(value, list)
        and bool(value)
        and all(isinstance(item, str) and item.strip() for item in value)
    )


def gate_packet(packet: dict) -> list[str]:
    """Return research blockers, adding free-render fields only when explicitly requested."""
    blockers = []
    required = [
        "topic",
        "why_selected",
        "trend_or_evergreen",
        "hook",
        "target_seconds",
        "sources",
        "unique_angle",
        "script_beats",
        "visual_plan",
        "audio_plan",
        "title",
        "hashtags",
        "prepublish_checklist",
    ]
    for key in required:
        if not packet.get(key):
            blockers.append("missing_" + key)

    if packet.get("free_render_requested") is True:
        for key in ("language", "content_type", "narration_text"):
            value = packet.get(key)
            if not isinstance(value, str) or not value.strip():
                blockers.append("missing_" + key)
        if not _valid_media_queries(packet.get("media_queries")):
            blockers.append("missing_media_queries")

    if is_duplicate(packet.get("title", ""), packet.get("hook", "")):
        blockers.append("duplicate_topic_or_hook")
    if packet.get("hook", "").lower().startswith(("merhaba", "bugün size", "bu videoda")):
        blockers.append("weak_intro_hook")
    sources = packet.get("sources") or []
    if len(sources) < 2:
        blockers.append("single_source")
    checklist = packet.get("prepublish_checklist") or {}
    critical = [
        "facts_verified",
        "sources_reliable",
        "strong_first_2s",
        "no_empty_intro",
        "audio_planned",
        "portrait_9_16_planned",
        "not_previously_published",
        "title_matches",
        "rights_ok",
        "publishable_quality_planned",
    ]
    for key in critical:
        if checklist.get(key) is not True:
            blockers.append("checklist_" + key)
    if packet.get("render_requested"):
        blockers.append("render_requested_before_gate")
    return blockers


def cmd_score(path: Path) -> int:
    data = load_json(path)
    ranked = rank(data.get("candidates") or [])
    out = {"schema": 1, "ranked": ranked, "selected": next((c for c in ranked if not c["veto"]), None)}
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0 if out["selected"] else 2


def cmd_dup(title: str, hook: str) -> int:
    dup = is_duplicate(title, hook)
    print(json.dumps({"duplicate": dup}, ensure_ascii=False))
    return 2 if dup else 0


def cmd_gate(path: Path) -> int:
    packet = load_json(path)
    blockers = gate_packet(packet)
    ready = not blockers
    print(json.dumps({"ready": ready, "blockers": blockers, "topic": packet.get("topic")}, ensure_ascii=False, indent=2))
    return 0 if ready else 2


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_score = sub.add_parser("score")
    p_score.add_argument("--input", type=Path, required=True)
    p_dup = sub.add_parser("check-duplicate")
    p_dup.add_argument("--title", default="")
    p_dup.add_argument("--hook", default="")
    p_gate = sub.add_parser("gate")
    p_gate.add_argument("--packet", type=Path, required=True)
    args = parser.parse_args()
    if args.cmd == "score":
        return cmd_score(args.input)
    if args.cmd == "check-duplicate":
        return cmd_dup(args.title, args.hook)
    return cmd_gate(args.packet)


if __name__ == "__main__":
    raise SystemExit(main())
