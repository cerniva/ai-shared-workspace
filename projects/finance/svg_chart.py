"""Finance chart without matplotlib/pandas: pure-Python SVG line chart + quality gate.

render_line_svg() draws verified series data to SVG. chart_gate() returns PASS
only when the file was actually rendered (exists, parses as SVG, one polyline
point per data point, non-degenerate bounds) and the data carries a source URL
and as-of time. Anything else is FAIL with reasons; there is no PASS without a
rendered file.
"""
from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

SVG_NS = "http://www.w3.org/2000/svg"
W, H, PAD = 640, 360, 48


def _check_series(series: dict[str, Any]) -> list[str]:
    problems = []
    points = series.get("points") or []
    if len(points) < 2:
        problems.append("need at least 2 points")
    for i, pt in enumerate(points):
        if not (isinstance(pt, (list, tuple)) and len(pt) == 2 and isinstance(pt[0], str)):
            problems.append(f"point {i} must be [label, value]")
            continue
        v = pt[1]
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
            problems.append(f"point {i} value not finite")
    if not str(series.get("source_url", "")).startswith("https://"):
        problems.append("source_url (https) required")
    if not series.get("as_of"):
        problems.append("as_of required")
    if not series.get("title"):
        problems.append("title required")
    return problems


def render_line_svg(series: dict[str, Any], out: Path) -> Path:
    problems = _check_series(series)
    if problems:
        raise ValueError("; ".join(problems))
    values = [float(v) for _, v in series["points"]]
    lo, hi = min(values), max(values)
    span = (hi - lo) or 1.0
    n = len(values)
    coords = [
        (PAD + (W - 2 * PAD) * i / (n - 1), H - PAD - (H - 2 * PAD) * (v - lo) / span)
        for i, v in enumerate(values)
    ]
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
    labels = series["points"]
    svg = (
        f'<svg xmlns="{SVG_NS}" width="{W}" height="{H}" viewBox="0 0 {W} {H}" data-points="{n}">\n'
        f'<rect width="{W}" height="{H}" fill="#ffffff"/>\n'
        f'<text x="{PAD}" y="28" font-family="sans-serif" font-size="16">{escape(series["title"])}</text>\n'
        f'<line x1="{PAD}" y1="{H - PAD}" x2="{W - PAD}" y2="{H - PAD}" stroke="#888"/>\n'
        f'<line x1="{PAD}" y1="{PAD}" x2="{PAD}" y2="{H - PAD}" stroke="#888"/>\n'
        f'<text x="4" y="{PAD + 4}" font-size="11">{hi:g}</text>\n'
        f'<text x="4" y="{H - PAD}" font-size="11">{lo:g}</text>\n'
        f'<text x="{PAD}" y="{H - PAD + 16}" font-size="11">{escape(labels[0][0])}</text>\n'
        f'<text x="{W - PAD}" y="{H - PAD + 16}" font-size="11" text-anchor="end">{escape(labels[-1][0])}</text>\n'
        f'<polyline fill="none" stroke="#1f5fbf" stroke-width="2" points="{poly}"/>\n'
        f'<text x="{PAD}" y="{H - 8}" font-size="10">Kaynak: {escape(series["source_url"])} | {escape(str(series["as_of"]))}</text>\n'
        "</svg>\n"
    )
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(svg, encoding="utf-8")
    return out


def chart_gate(svg_path: Path, series: dict[str, Any]) -> dict[str, Any]:
    reasons = _check_series(series)
    path = Path(svg_path)
    if not path.exists() or path.stat().st_size == 0:
        reasons.append("chart file not rendered")
    else:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            root = None
            reasons.append(f"svg does not parse: {exc}")
        if root is not None:
            if root.tag != f"{{{SVG_NS}}}svg":
                reasons.append("root is not svg")
            lines = root.findall(f"{{{SVG_NS}}}polyline")
            if len(lines) != 1:
                reasons.append("expected exactly one polyline")
            else:
                pts = lines[0].get("points", "").split()
                if len(pts) != len(series.get("points") or []):
                    reasons.append(f"polyline has {len(pts)} points, data has {len(series.get('points') or [])}")
                ys = {p.split(",")[1] for p in pts if "," in p}
                if len(ys) < 2 and len(set(v for _, v in series.get("points") or [])) > 1:
                    reasons.append("flat line for non-flat data")
            if series.get("source_url") and series["source_url"] not in "".join(root.itertext()):
                reasons.append("source not printed on chart")
    return {"status": "FAIL" if reasons else "PASS", "reasons": reasons, "path": str(path)}
