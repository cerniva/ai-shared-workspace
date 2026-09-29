#!/usr/bin/env python3
"""Canonical local health logging and independent Shorts publish health."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable


def append_local_event(path: str | Path, event: dict, *, external_sink: Callable[[dict], None] | None = None) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    if external_sink is not None:
        try:
            external_sink(event)
        except Exception:
            # Optional dashboards must never break canonical local recording.
            pass


def combine_short_health(*, production: str, preflight: str, publish: str) -> dict[str, str]:
    overall = "healthy" if production == "healthy" and preflight == "healthy" else "failed"
    return {
        "production": production,
        "preflight": preflight,
        "publish": publish,
        "overall_production": overall,
    }
