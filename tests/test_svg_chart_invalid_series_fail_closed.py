"""chart_gate must fail closed (status FAIL) for invalid source series instead of raising.

Regression for branch fix/svg-chart-gate-invalid-series-20261017 (1ddd385).
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "projects" / "finance"))
import svg_chart  # noqa: E402

GOOD = {"title": "t", "source_url": "https://example.org/data", "as_of": "2026-10-17",
        "points": [["2026-01", 1.0], ["2026-02", 3.0], ["2026-03", 2.0]]}


def _bad(value):
    s = dict(GOOD)
    s["points"] = [["2026-01", 1.0], ["2026-02", value], ["2026-03", 2.0]]
    return s


@pytest.mark.parametrize("value", ["invalid", None, float("nan"), float("inf"), True])
def test_invalid_point_value_returns_fail_not_exception(tmp_path, value):
    out = svg_chart.render_line_svg(GOOD, tmp_path / "c.svg")
    res = svg_chart.chart_gate(out, _bad(value))
    assert res["status"] == "FAIL", res
    assert any("point 1" in r for r in res["reasons"]), res


def test_malformed_point_shape_returns_fail(tmp_path):
    out = svg_chart.render_line_svg(GOOD, tmp_path / "c.svg")
    s = dict(GOOD)
    s["points"] = [["2026-01", 1.0], "oops", ["2026-03", 2.0]]
    res = svg_chart.chart_gate(out, s)
    assert res["status"] == "FAIL", res


def test_valid_series_still_passes(tmp_path):
    out = svg_chart.render_line_svg(GOOD, tmp_path / "c.svg")
    assert svg_chart.chart_gate(out, GOOD)["status"] == "PASS"
