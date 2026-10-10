#!/usr/bin/env python3
"""Weekly Shorts learning note from TinyFish YouTube Studio analytics output.

Reads the JSON printed by ``scripts/tinyfish_youtube.py analytics --execute``
(``{"status", "run_id", "result": {...}}``) and writes a dated learning note
``knowledge/shorts/learnings/weekly-YYYY-WW.md`` with concrete takeaways.

Only real data: if the run is not COMPLETED, NOT_SIGNED_IN, or required
fields are missing, no note is written and the script exits 2.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_DIR = Path("knowledge/shorts/learnings")
REQUIRED = ("channel_name", "period", "views")


class NoRealData(ValueError):
    pass


def extract_metrics(doc: dict[str, Any]) -> dict[str, Any]:
    """Validate a tinyfish analytics document and return its result block."""
    if not isinstance(doc, dict):
        raise NoRealData("analytics output is not a JSON object")
    if doc.get("dry_run"):
        raise NoRealData("analytics output is a dry-run request, not data")
    status = doc.get("status")
    if status != "COMPLETED":
        raise NoRealData(f"analytics run status is {status!r}, not COMPLETED")
    result = doc.get("result")
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError as exc:
            raise NoRealData("result is not JSON") from exc
    if not isinstance(result, dict):
        raise NoRealData("result block missing")
    if "NOT_SIGNED_IN" in json.dumps(result):
        raise NoRealData("YouTube Studio profile NOT_SIGNED_IN")
    missing = [k for k in REQUIRED if result.get(k) in (None, "")]
    if missing:
        raise NoRealData("missing required fields: " + ",".join(missing))
    if not isinstance(result.get("views"), (int, float)):
        raise NoRealData("views is not a number")
    return result


def _fmt(n: Any) -> str:
    if isinstance(n, float) and not n.is_integer():
        return f"{n:,.1f}"
    return f"{int(n):,}" if isinstance(n, (int, float)) else "n/a"


def takeaways(m: dict[str, Any], prev: dict[str, Any] | None = None) -> list[str]:
    out: list[str] = []
    views = float(m["views"])
    top = [v for v in (m.get("top_videos") or []) if isinstance(v, dict) and isinstance(v.get("views"), (int, float))]
    top.sort(key=lambda v: v["views"], reverse=True)
    if top and views > 0:
        lead = top[0]
        share = lead["views"] / views * 100
        out.append(
            f"Top video \"{lead.get('title', '?')}\" drew {share:.0f}% of channel views "
            f"({_fmt(lead['views'])}/{_fmt(views)}). Next Short: reuse its topic family and hook shape "
            "(question in first 3 s), but with original/licensed moving footage."
        )
        if len(top) >= 3:
            top3 = sum(v["views"] for v in top[:3]) / views * 100
            out.append(
                f"Top 3 videos = {top3:.0f}% of views; the long tail is weak. Prefer 2-3 repeatable series "
                "over one-off topics; titles of the top 3: " + "; ".join(str(v.get("title", "?")) for v in top[:3]) + "."
            )
        if len(top) >= 2 and top[1]["views"] > 0:
            ratio = top[0]["views"] / top[1]["views"]
            out.append(f"#1 outperformed #2 by {ratio:.1f}x; test one variable at a time (hook vs topic) to see which drove it.")
    likes = m.get("likes")
    if isinstance(likes, (int, float)) and views > 0:
        lk = likes / views * 1000
        out.append(f"Likes {_fmt(likes)} ({lk:.1f} per 1k views). "
                   + ("Low resonance: sharpen the curiosity gap/topic." if lk < 30 else "Topic resonates; build a follow-up series."))
    stw = m.get("stayed_to_watch_percent")
    if isinstance(stw, (int, float)):
        out.append(f"Stayed to watch (viewed vs swiped away): {stw:.0f}%. "
                   + ("Under 60%: the first 1-2 s are losing the feed; open on motion + the question." if stw < 60
                      else "Hook holds the feed; iterate on mid-video retention."))
    else:
        out.append("Stayed-to-watch (swipe-away) not available in this data; read it in Studio before judging the hook.")
    wt = m.get("watch_time_hours")
    if isinstance(wt, (int, float)) and views > 0:
        sec_per_view = wt * 3600 / views
        out.append(
            f"Average ~{sec_per_view:.1f} s watched per view ({_fmt(wt)} h / {_fmt(views)} views). "
            + ("Below ~10 s: front-load the payoff and keep Shorts <=30 s with a loop ending."
               if sec_per_view < 10 else "Retention per view is healthy; keep the 30 s format and test a stronger mid-point beat.")
        )
    subs = m.get("subscribers_change")
    if isinstance(subs, (int, float)) and views > 0:
        per_k = subs / views * 1000
        out.append(
            f"Subscribers {subs:+.0f} ({per_k:.2f} per 1k views). "
            + ("Conversion is low: add a series promise in the last 2 s (\"part 2 / next tip\")."
               if per_k < 2 else "Conversion is fine; keep the series format.")
        )
    if prev:
        pv = prev.get("views")
        if isinstance(pv, (int, float)) and pv > 0:
            out.append(f"Views vs previous note: {(views - pv) / pv * 100:+.0f}% ({_fmt(pv)} -> {_fmt(views)}). Same period window required for a fair compare.")
    out.append(
        "Caveat: view counts alone are not retention evidence; check engaged views, stayed-to-watch and "
        "average percentage viewed in Studio before concluding causality."
    )
    return out


def render_note(m: dict[str, Any], *, run_id: str | None, source: str, today: dt.date,
                prev: dict[str, Any] | None = None) -> str:
    year, week, _ = today.isocalendar()
    lines = [
        f"# Shorts weekly learning — {year}-W{week:02d}",
        "",
        f"- Generated: {today.isoformat()}",
        f"- Channel: {m['channel_name']}",
        f"- Period: {m['period']}",
        f"- Source: {source}" + (f" (TinyFish run {run_id})" if run_id else ""),
        "",
        "## Metrics",
        "",
        f"- Views: {_fmt(m['views'])}",
        f"- Watch time (h): {_fmt(m.get('watch_time_hours'))}",
        f"- Subscriber change: {_fmt(m.get('subscribers_change'))}",
        f"- Likes: {_fmt(m.get('likes'))}",
        f"- Engaged views: {_fmt(m.get('engaged_views'))}",
        f"- Stayed to watch %: {_fmt(m.get('stayed_to_watch_percent'))}",
        "",
        "| # | Video | Views |",
        "|---|---|---|",
    ]
    for i, v in enumerate(m.get("top_videos") or [], start=1):
        if isinstance(v, dict):
            lines.append(f"| {i} | {v.get('title', '?')} | {_fmt(v.get('views'))} |")
    lines += ["", "## Takeaways for future Shorts", ""]
    lines += [f"{i}. {t}" for i, t in enumerate(takeaways(m, prev), start=1)]
    lines.append("")
    return "\n".join(lines)


def merge_api(metrics: dict[str, Any] | None, api_doc: Any) -> dict[str, Any] | None:
    """Fill gaps from youtube_video_metrics.py output; API-only data is accepted if real."""
    api = api_doc.get("metrics") if isinstance(api_doc, dict) and api_doc.get("status") == "COMPLETED" else None
    if not api or not api.get("has_data"):
        return metrics
    merged = dict(metrics) if metrics else {
        "channel_name": "own channel (Analytics API)",
        "period": f"{api_doc.get('start')} to {api_doc.get('end')}", "views": api.get("views")}
    pairs = {"views": "views", "watch_time_hours": "watch_time_hours", "subscribers_change": "subscribersGained",
             "likes": "likes", "engaged_views": "engagedViews"}
    for ours, theirs in pairs.items():
        if merged.get(ours) is None and api.get(theirs) is not None:
            merged[ours] = api[theirs]
    if not isinstance(merged.get("views"), (int, float)):
        return metrics
    return merged


def note_path(out_dir: Path, today: dt.date) -> Path:
    year, week, _ = today.isocalendar()
    return out_dir / f"weekly-{year}-{week:02d}.md"


def _previous_metrics(out_dir: Path, current: Path) -> dict[str, Any] | None:
    sidecars = sorted(p for p in out_dir.glob("weekly-*.json") if p.with_suffix(".md") != current)
    if not sidecars:
        return None
    try:
        return json.loads(sidecars[-1].read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("analytics_json", type=Path, help="artifacts/youtube_analytics.json")
    p.add_argument("--out-dir", type=Path, default=DEFAULT_DIR)
    p.add_argument("--date", help="YYYY-MM-DD (default: today)")
    p.add_argument("--api-metrics", type=Path, help="youtube_video_metrics.py output (optional)")
    p.add_argument("--source", default="tinyfish-youtube-analytics workflow artifact")
    args = p.parse_args(argv)
    today = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    doc: dict[str, Any] = {}
    metrics = None
    reason = ""
    try:
        doc = json.loads(args.analytics_json.read_text(encoding="utf-8"))
        metrics = extract_metrics(doc)
    except (OSError, ValueError) as exc:
        reason = str(exc)
    if args.api_metrics:
        try:
            metrics = merge_api(metrics, json.loads(args.api_metrics.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    if metrics is None:
        print(json.dumps({"ok": False, "written": None, "reason": reason or "no real data"}))
        return 2
    if not isinstance(doc, dict):
        doc = {}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    path = note_path(args.out_dir, today)
    prev = _previous_metrics(args.out_dir, path)
    path.write_text(render_note(metrics, run_id=doc.get("run_id"), source=args.source, today=today, prev=prev), encoding="utf-8")
    path.with_suffix(".json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "written": str(path)}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
