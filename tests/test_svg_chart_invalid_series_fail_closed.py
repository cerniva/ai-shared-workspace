"""chart_gate must fail closed (status FAIL) for invalid source series instead of raising.

Regression for branch fix/svg-chart-gate-invalid-series-20261017 (1ddd385).
Written with stdlib unittest (no pytest import) so the unittest-based
worker-orchestration-tests CI job can load it; pytest still collects it.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "projects" / "finance"))
import svg_chart  # noqa: E402

GOOD = {"title": "t", "source_url": "https://example.org/data", "as_of": "2026-10-17",
        "points": [["2026-01", 1.0], ["2026-02", 3.0], ["2026-03", 2.0]]}


def _bad(value):
    s = dict(GOOD)
    s["points"] = [["2026-01", 1.0], ["2026-02", value], ["2026-03", 2.0]]
    return s


class SvgChartInvalidSeriesFailClosedTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_invalid_point_value_returns_fail_not_exception(self):
        for value in ["invalid", None, float("nan"), float("inf"), True]:
            with self.subTest(value=value):
                out = svg_chart.render_line_svg(GOOD, self.tmp_path / "c.svg")
                res = svg_chart.chart_gate(out, _bad(value))
                self.assertEqual(res["status"], "FAIL", res)
                self.assertTrue(any("point 1" in r for r in res["reasons"]), res)

    def test_malformed_point_shape_returns_fail(self):
        out = svg_chart.render_line_svg(GOOD, self.tmp_path / "c.svg")
        s = dict(GOOD)
        s["points"] = [["2026-01", 1.0], "oops", ["2026-03", 2.0]]
        res = svg_chart.chart_gate(out, s)
        self.assertEqual(res["status"], "FAIL", res)

    def test_valid_series_still_passes(self):
        out = svg_chart.render_line_svg(GOOD, self.tmp_path / "c.svg")
        self.assertEqual(svg_chart.chart_gate(out, GOOD)["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
