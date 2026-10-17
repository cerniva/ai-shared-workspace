"""chart_gate must reject a polyline whose y-values don't match the data (branch ee82166).

Converted to stdlib unittest so worker-orchestration-tests (unittest discover) collects all 7 SVG regression tests.
"""
import re
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "projects" / "finance"))
import svg_chart  # noqa: E402

SERIES = {"title": "t", "source_url": "https://example.org/data", "as_of": "2026-10-17", "points": [["2026-01", 1.0], ["2026-02", 3.0], ["2026-03", 2.0]]}


class SvgChartValueGateTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_rendered_chart_passes_value_gate(self):
        out = svg_chart.render_line_svg(SERIES, self.tmp_path / "c.svg")
        res = svg_chart.chart_gate(out, SERIES)
        self.assertEqual(res["status"], "PASS", res)

    def test_tampered_y_value_is_rejected(self):
        out = svg_chart.render_line_svg(SERIES, self.tmp_path / "c.svg")
        txt = out.read_text()
        m = re.search(r'<polyline[^>]* points="([^"]+)"', txt)
        pts = m.group(1).split()
        x, y = pts[1].split(",")
        pts[1] = f"{x},{float(y) + 25:.1f}"
        out.write_text(txt.replace(m.group(1), " ".join(pts)))
        res = svg_chart.chart_gate(out, SERIES)
        self.assertTrue(any("y[1]" in r for r in res.get("reasons", [])), res)

    def _tamper(self, out, idx, fn):
        txt = out.read_text()
        m = re.search(r'<polyline[^>]* points="([^"]+)"', txt)
        pts = m.group(1).split()
        x, y = pts[idx].split(",")
        pts[idx] = fn(x, y)
        out.write_text(txt.replace(m.group(1), " ".join(pts)))

    def test_tampered_x_value_is_rejected(self):
        out = svg_chart.render_line_svg(SERIES, self.tmp_path / "c.svg")
        self._tamper(out, 1, lambda x, y: f"{float(x) + 40:.1f},{y}")
        res = svg_chart.chart_gate(out, SERIES)
        self.assertTrue(any("x[1]" in r for r in res.get("reasons", [])), res)

    def test_nonfinite_point_is_rejected(self):
        out = svg_chart.render_line_svg(SERIES, self.tmp_path / "c.svg")
        self._tamper(out, 2, lambda x, y: f"nan,{y}")
        res = svg_chart.chart_gate(out, SERIES)
        self.assertEqual(res["status"], "FAIL")
        self.assertTrue(any("not finite" in r for r in res.get("reasons", [])), res)


if __name__ == "__main__":
    unittest.main()
