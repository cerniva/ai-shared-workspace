"""HO-20261010-10 finance repair: state read-back, fallback channel, SVG chart gate, altcoin panel."""
from __future__ import annotations

import io
import json
import math
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from projects.finance import altcoin_panel as ap
from projects.finance import state_store as ss
from projects.finance.svg_chart import chart_gate, render_line_svg
from scripts import grok_fallback_channel as ch

ROOT = Path(__file__).resolve().parents[1]
BASE = {"schema_version": 1, "sources": [{"source_id": "s1"}], "learnings": [{"learning_id": "l1"}]}


class StateStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "state.json"
        self.path.write_bytes(ss.dumps(BASE))

    def tearDown(self):
        self.tmp.cleanup()

    def test_repo_state_file_is_valid(self):
        doc, _ = ss.load(ROOT / "knowledge" / "finance_runtime_state.json")
        self.assertGreater(ss.validate(doc)["sources"], 0)

    def test_save_dedups_and_reads_back(self):
        _, sha = ss.load(self.path)
        res = ss.save(self.path, sha, lambda d: (ss.upsert(d["sources"], {"source_id": "s1"}, "source_id"),
                                                ss.upsert(d["sources"], {"source_id": "s2"}, "source_id")))
        self.assertEqual(res["counts"], {"sources": 2, "learnings": 1})
        self.assertEqual(ss.digest(self.path.read_bytes()), res["sha256"])

    def test_concurrent_change_is_reapplied_once_without_loss(self):
        _, stale = ss.load(self.path)
        other = json.loads(self.path.read_text()); other["sources"].append({"source_id": "s9"})
        self.path.write_bytes(ss.dumps(other))
        res = ss.save(self.path, stale, lambda d: ss.upsert(d["sources"], {"source_id": "s2"}, "source_id"))
        self.assertEqual(res["attempt"], 1)
        ids = {r["source_id"] for r in json.loads(self.path.read_text())["sources"]}
        self.assertEqual(ids, {"s1", "s2", "s9"})

    def test_dropping_rows_or_duplicates_is_refused(self):
        _, sha = ss.load(self.path)
        before = self.path.read_bytes()
        with self.assertRaises(ss.StateError):
            ss.save(self.path, sha, lambda d: d["sources"].clear())
        with self.assertRaises(ss.StateError):
            ss.save(self.path, sha, lambda d: d["sources"].append({"source_id": "s1"}))
        self.assertEqual(self.path.read_bytes(), before)

    def test_malformed_state_fails_verify(self):
        self.path.write_text("{bad")
        self.assertEqual(ss.main(["verify", "--path", str(self.path)]), 1)


class ChannelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_post_inbox_ack_roundtrip(self):
        at = datetime(2026, 10, 10, 0, 0, 0, tzinfo=timezone.utc)
        msg = ch.post("chatgpt", "grok", "Finans", "Gmail blocked; please verify state.", "finance", self.dir, at)
        self.assertEqual(msg["id"], "FB-20261010-000000-chatgpt-finance")
        self.assertEqual([m["id"] for m in ch.inbox("grok", self.dir)], [msg["id"]])
        with self.assertRaises(ch.ChannelError):
            ch.ack(msg["id"], "chatgpt", self.dir)
        ch.ack(msg["id"], "grok", self.dir)
        self.assertEqual(ch.inbox("grok", self.dir), [])

    def test_rejects_secrets_bad_actor_and_duplicates(self):
        at = datetime(2026, 10, 10, tzinfo=timezone.utc)
        with self.assertRaises(ch.ChannelError):
            ch.post("chatgpt", "grok", "x", "token ghp_abc", "s", self.dir, at)
        with self.assertRaises(ch.ChannelError):
            ch.post("grok", "grok", "x", "y", "s", self.dir, at)
        ch.post("grok", "chatgpt", "x", "y", "s", self.dir, at)
        with self.assertRaises(ch.ChannelError):
            ch.post("grok", "chatgpt", "x", "y", "s", self.dir, at)

    def test_repo_channel_validates(self):
        self.assertEqual(ch.main(["validate"]), 0)


SERIES = {"title": "USD/TRY (TCMB döviz satış)", "source_url": "https://www.tcmb.gov.tr/kurlar/today.xml",
          "as_of": "2026-10-01", "points": [["29.09", 48.90], ["30.09", 48.97], ["01.10", 49.03]]}


class ChartGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = Path(self.tmp.name) / "c.svg"

    def tearDown(self):
        self.tmp.cleanup()

    def test_rendered_chart_passes(self):
        render_line_svg(SERIES, self.out)
        self.assertEqual(chart_gate(self.out, SERIES), {"status": "PASS", "reasons": [], "path": str(self.out)})

    def test_no_file_no_pass(self):
        self.assertEqual(chart_gate(self.out, SERIES)["status"], "FAIL")

    def test_point_mismatch_and_missing_source_fail(self):
        render_line_svg(SERIES, self.out)
        more = dict(SERIES, points=SERIES["points"] + [["02.10", 49.1]])
        self.assertIn("polyline has 3 points, data has 4", chart_gate(self.out, more)["reasons"])
        with self.assertRaises(ValueError):
            render_line_svg(dict(SERIES, source_url=""), self.out)
        with self.assertRaises(ValueError):
            render_line_svg(dict(SERIES, points=[["a", float("nan")], ["b", 1]]), self.out)

    def test_no_forbidden_libraries(self):
        for rel in ("projects/finance/svg_chart.py", "projects/finance/altcoin_panel.py"):
            text = (ROOT / rel).read_text(encoding="utf-8")
            for lib in ("matplotlib", "pandas", "seaborn"):
                self.assertNotIn(f"import {lib}", text)


def _series(n, start, step, vol=1000.0):
    return [start * (1 + step) ** i for i in range(n)], [vol + 10 * i for i in range(n)]


class AltcoinPanelTests(unittest.TestCase):
    def setUp(self):
        self.src = ap.FixtureSource({"bitcoin": _series(120, 60000, 0.001), "solana": _series(120, 100, 0.01)})

    def test_ten_indicators_scores_na_without_calibration(self):
        out = ap.panel("solana", self.src)
        self.assertEqual(out["status"], "OK")
        self.assertEqual(len(out["indicators"]), 10)
        self.assertTrue(all(r["score"] == "N/A" for r in out["indicators"].values()))
        self.assertEqual(out["composite_score"], "N/A")
        self.assertAlmostEqual(out["indicators"]["return_7d"]["value"], 1.01 ** 7 - 1, places=6)
        self.assertEqual(out["indicators"]["rsi14"]["value"], 100.0)
        self.assertGreater(out["indicators"]["rel_strength_vs_btc_30d"]["value"], 0)

    def test_validated_calibration_scores_and_unvalidated_does_not(self):
        cal = {n: {"lo": -1, "hi": 1, "validated": True} for n in ap.INDICATORS}
        cal["rsi14"] = {"lo": 0, "hi": 100, "validated": True}
        cal["volatility_30d"] = {"lo": 0, "hi": 2, "direction": "lower_is_bullish", "validated": True}
        out = ap.panel("solana", self.src, cal)
        self.assertNotEqual(out["composite_score"], "N/A")
        self.assertEqual(out["indicators"]["rsi14"]["score"], 100.0)
        self.assertEqual(ap.score(0.5, {"lo": 0, "hi": 1}), "N/A")

    def test_insufficient_data(self):
        src = ap.FixtureSource({"bitcoin": _series(30, 1, 0.01), "x": _series(30, 1, 0.01)})
        self.assertEqual(ap.panel("x", src)["status"], "INSUFFICIENT_DATA")

    def test_coingecko_source_parses_without_key(self):
        seen = {}

        class Resp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def opener(req, timeout):
            seen["url"], seen["headers"] = req.full_url, dict(req.header_items())
            return Resp(json.dumps({"prices": [[0, 1.0], [1, 2.0]], "total_volumes": [[0, 5.0], [1, 6.0]]}).encode())

        closes, vols = ap.CoinGeckoSource(opener).closes_volumes("solana", 91)
        self.assertEqual((closes, vols), ([1.0, 2.0], [5.0, 6.0]))
        self.assertIn("/coins/solana/market_chart", seen["url"])
        self.assertFalse(any("key" in h.lower() for h in seen["headers"]))


if __name__ == "__main__":
    unittest.main()
