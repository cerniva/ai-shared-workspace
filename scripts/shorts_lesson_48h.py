#!/usr/bin/env python3
"""48-hour post-upload lesson loop for Shorts.

Ledger: knowledge/shorts/upload_ledger.json  ({"uploads": [{video_id, uploaded_at, ...}]})
- ``record``: append an upload (called by youtube-upload.yml after a verified upload).
- ``due``: list uploads whose 48h mark has passed and that have no lesson yet.
- ``run``: for each due upload fetch metrics (youtube_video_metrics.fetch), append a
  lesson to knowledge/shorts/learnings/video-lessons.md and mark the ledger entry.
  Uploads whose metrics are blocked stay due (attempts counted), no fake lesson.
Never uploads or publishes.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge" / "shorts" / "upload_ledger.json"
LESSONS = ROOT / "knowledge" / "shorts" / "learnings" / "video-lessons.md"
DELAY = dt.timedelta(hours=48)


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _parse(ts: str) -> dt.datetime:
    t = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


def load(path: Path = LEDGER) -> dict[str, Any]:
    if not path.is_file():
        return {"schema": 1, "uploads": []}
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not isinstance(doc.get("uploads"), list):
        raise ValueError("upload ledger must be an object with an uploads list")
    return doc


def save(doc: dict[str, Any], path: Path = LEDGER) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record(doc: dict[str, Any], video_id: str, uploaded_at: str, **extra: Any) -> dict[str, Any]:
    if not video_id or not isinstance(video_id, str):
        raise ValueError("video_id required")
    _parse(uploaded_at)
    if any(u.get("video_id") == video_id for u in doc["uploads"]):
        return doc
    doc["uploads"].append({"video_id": video_id, "uploaded_at": uploaded_at,
                           **{k: v for k, v in extra.items() if v not in (None, "")},
                           "lesson_at": None, "attempts": 0})
    return doc


def due(doc: dict[str, Any], now: dt.datetime | None = None) -> list[dict[str, Any]]:
    now = now or _now()
    return [u for u in doc["uploads"] if not u.get("lesson_at") and _parse(u["uploaded_at"]) + DELAY <= now]


def lesson_text(entry: dict[str, Any], result: dict[str, Any], now: dt.datetime) -> str:
    m = result["metrics"]
    def f(k):
        v = m.get(k)
        return "n/a" if v is None else (f"{v:,.2f}" if isinstance(v, float) else f"{v:,}")
    takeaways = []
    avp = m.get("averageViewPercentage")
    if isinstance(avp, (int, float)):
        takeaways.append("Average % viewed >= 70: keep this hook/pacing pattern." if avp >= 70 else
                         "Average % viewed < 70: front-load the payoff, cut 3-5 s, tighten beats.")
    lk = m.get("likes_per_1k_views")
    if isinstance(lk, (int, float)):
        takeaways.append("Likes/1k views >= 30: topic resonates; make a series follow-up." if lk >= 30 else
                         "Likes/1k views < 30: topic/angle weak; test a sharper curiosity gap.")
    er = m.get("engaged_ratio")
    if isinstance(er, (int, float)):
        takeaways.append(f"Engaged/views ratio {er:.2f} (API proxy, not Studio stayed-to-watch).")
    if not m.get("has_data"):
        takeaways.append("API returned no rows yet (data lag); re-check in the weekly note.")
    lines = [
        f"## {entry['video_id']} — 48h lesson ({now.date().isoformat()})",
        "",
        f"- Uploaded: {entry['uploaded_at']}" + (f" | packet: {entry['packet']}" if entry.get("packet") else "")
        + (f" | title: {entry['title']}" if entry.get("title") else ""),
        f"- Window: {result['start']} → {result['end']} (source: {result['source']})",
        f"- Views {f('views')} | engaged {f('engagedViews')} | watch h {f('watch_time_hours')} | "
        f"avg dur s {f('averageViewDuration')} | avg % {f('averageViewPercentage')} | likes {f('likes')} "
        f"| likes/1k {f('likes_per_1k_views')} | subs +{f('subscribersGained')}",
        "- Stayed-to-watch (swipe): not in API; read from Studio/TinyFish.",
        "",
        *[f"- Lesson: {t}" for t in takeaways],
        "",
    ]
    return "\n".join(lines)


def run(doc: dict[str, Any], fetcher: Callable[..., dict[str, Any]], lessons: Path = LESSONS,
        now: dt.datetime | None = None) -> list[str]:
    now = now or _now()
    written = []
    for entry in due(doc, now):
        start = _parse(entry["uploaded_at"]).date()
        result = fetcher(entry["video_id"], start, now.date())
        entry["attempts"] = int(entry.get("attempts", 0)) + 1
        if result.get("status") != "COMPLETED":
            entry["last_error"] = result.get("reason_code")
            continue
        lessons.parent.mkdir(parents=True, exist_ok=True)
        if not lessons.exists():
            lessons.write_text("# Shorts 48h video lessons\n\nAppended by shorts-48h-lessons workflow. Real API data only.\n\n", encoding="utf-8")
        with lessons.open("a", encoding="utf-8") as fh:
            fh.write(lesson_text(entry, result, now) + "\n")
        entry["lesson_at"] = now.isoformat(timespec="seconds")
        entry["metrics_48h"] = result["metrics"]
        entry.pop("last_error", None)
        written.append(entry["video_id"])
    return written


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--video-id", required=True)
    r.add_argument("--uploaded-at", default=None)
    r.add_argument("--title")
    r.add_argument("--packet")
    r.add_argument("--run-id")
    sub.add_parser("due")
    sub.add_parser("run")
    for s in sub.choices.values():
        s.add_argument("--ledger", type=Path, default=LEDGER)
    a = p.parse_args(argv)
    doc = load(a.ledger)
    if a.cmd == "record":
        record(doc, a.video_id, a.uploaded_at or _now().isoformat(timespec="seconds"),
               title=a.title, packet=a.packet, run_id=a.run_id)
        save(doc, a.ledger)
        print(json.dumps({"ok": True, "recorded": a.video_id}))
        return 0
    if a.cmd == "due":
        print(json.dumps({"due": [u["video_id"] for u in due(doc)]}))
        return 0
    sys.path.insert(0, str(ROOT / "scripts"))
    import youtube_video_metrics
    written = run(doc, youtube_video_metrics.fetch)
    save(doc, a.ledger)
    print(json.dumps({"ok": True, "lessons_written": written,
                      "still_due": [u["video_id"] for u in due(doc)]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
