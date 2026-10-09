#!/usr/bin/env python3
"""Apply video_shopify plan learnings (artifacts/plan_learnings.json) to a Shorts build.

Each required learning_id maps to a concrete rule that changes or gates the
render manifest. A build with a missing, errored or incomplete learnings file
fails with ``bridge_failure`` instead of silently ignoring the knowledge loop.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

PRIVACY = "learn_af28044522e96790"   # explicit privacyStatus=private + madeForKids + synthetic flags
QUOTA = "learn_f6b1a61d4538f86b"     # videos.insert 100/day bucket, reset 00:00 PT
CERNO = "learn_53ca8fb858703eb6"     # 30-second moving-footage concept tests, no broadcast clips
HO04_GATE = "learn_ae8a18babc190373"  # hook/storyboard/rights/MP4 QC before publish

MAX_CONCEPT_SECONDS = 30.0


class LearningsError(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise LearningsError(f"bridge_failure: plan learnings file missing: {path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise LearningsError("bridge_failure: plan learnings file is not valid JSON") from exc
    if not isinstance(doc, dict) or doc.get("error") or not isinstance(doc.get("learnings"), list):
        raise LearningsError(f"bridge_failure: plan learnings unusable: {doc.get('error') if isinstance(doc, dict) else 'bad shape'}")
    if doc.get("tag") != "video_shopify":
        raise LearningsError(f"bridge_failure: expected video_shopify learnings, got {doc.get('tag')!r}")
    return doc


def _privacy(packet: dict, m: dict) -> None:
    kids = packet.get("made_for_kids", False)
    if not isinstance(kids, bool):
        raise LearningsError("made_for_kids must be true/false (explicit privacy gate)")
    m["upload_policy"].update({"privacyStatus": "private", "selfDeclaredMadeForKids": kids,
                               "containsSyntheticMedia": True})


def _quota(packet: dict, m: dict) -> None:
    m["upload_policy"]["quota"] = {"bucket": "videos.insert", "daily_uploads": 100,
                                   "count_failed_calls": True, "reset": "00:00 America/Los_Angeles"}


def _cerno(packet: dict, m: dict) -> None:
    if float(m["target_seconds"]) > MAX_CONCEPT_SECONDS:
        raise LearningsError(f"{CERNO}: concept tests are max {MAX_CONCEPT_SECONDS:g}s, packet asks {m['target_seconds']}")
    if packet.get("uses_broadcast_clips"):
        raise LearningsError(f"{CERNO}: copyrighted broadcast clips are not allowed")
    m["production_gates"]["moving_footage_only"] = True


def _ho04(packet: dict, m: dict) -> None:
    m["production_gates"].update({"hook_storyboard_qc_required": True, "rights_qc_required": True,
                                  "full_mp4_qc_required": True})


RULES: dict[str, Callable[[dict, dict], None]] = {PRIVACY: _privacy, QUOTA: _quota, CERNO: _cerno, HO04_GATE: _ho04}


def apply(doc: dict[str, Any], packet: dict, manifest: dict) -> list[str]:
    """Mutate manifest per learnings; return applied learning ids. Missing required id -> error."""
    present = {row.get("learning_id") for row in doc["learnings"] if isinstance(row, dict)}
    missing = sorted(set(RULES) - present)
    if missing:
        raise LearningsError("bridge_failure: required learnings missing: " + ", ".join(missing))
    manifest.setdefault("upload_policy", {})
    manifest.setdefault("production_gates", {})
    applied = []
    for learning_id, rule in RULES.items():
        rule(packet, manifest)
        applied.append(learning_id)
    manifest["applied_learning_ids"] = applied
    return applied
