"""chart_gate must reject a polyline whose y-values don't match the data (branch ee82166)."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "projects" / "finance"))
import svg_chart  # noqa: E402

SERIES = {"title": "t", "source_url": "https://example.org/data", "as_of": "2026-10-17", "points": [["2026-01", 1.0], ["2026-02", 3.0], ["2026-03", 2.0]]}


def test_rendered_chart_passes_value_gate(tmp_path):
    out = svg_chart.render_line_svg(SERIES, tmp_path / "c.svg")
    res = svg_chart.chart_gate(out, SERIES)
    assert res["status"] == "PASS", res


def test_tampered_y_value_is_rejected(tmp_path):
    out = svg_chart.render_line_svg(SERIES, tmp_path / "c.svg")
    txt = out.read_text()
    m = re.search(r'<polyline[^>]* points="([^"]+)"', txt)
    pts = m.group(1).split()
    x, y = pts[1].split(",")
    pts[1] = f"{x},{float(y) + 25:.1f}"
    out.write_text(txt.replace(m.group(1), " ".join(pts)))
    res = svg_chart.chart_gate(out, SERIES)
    assert any("y[1]" in r for r in res.get("reasons", [])), res


def _tamper(out, idx, fn):
    txt = out.read_text()
    m = re.search(r'<polyline[^>]* points="([^"]+)"', txt)
    pts = m.group(1).split()
    x, y = pts[idx].split(",")
    pts[idx] = fn(x, y)
    out.write_text(txt.replace(m.group(1), " ".join(pts)))


def test_tampered_x_value_is_rejected(tmp_path):
    out = svg_chart.render_line_svg(SERIES, tmp_path / "c.svg")
    _tamper(out, 1, lambda x, y: f"{float(x) + 40:.1f},{y}")
    res = svg_chart.chart_gate(out, SERIES)
    assert any("x[1]" in r for r in res.get("reasons", [])), res


def test_nonfinite_point_is_rejected(tmp_path):
    out = svg_chart.render_line_svg(SERIES, tmp_path / "c.svg")
    _tamper(out, 2, lambda x, y: f"nan,{y}")
    res = svg_chart.chart_gate(out, SERIES)
    assert res["status"] == "FAIL"
    assert any("not finite" in r for r in res.get("reasons", [])), res
