"""Finance altseason decision consumer: active learning -> real panel output.

Uses only local canonical ledger/catalog copies and synthetic input values.
No trading, remote market requests, or PayoutLens access.
"""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from projects.finance import altcoin_panel as panel
from scripts.knowledge_bridge import CatalogError, DEFAULT_CATALOG
from scripts.learning_bridge import DEFAULT_LEDGER


class AltseasonLearningConsumerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.ledger = root / "learning_ledger.json"
        self.catalog = root / "source_catalog.json"
        shutil.copyfile(DEFAULT_LEDGER, self.ledger)
        shutil.copyfile(DEFAULT_CATALOG, self.catalog)
        self.cfg = panel.load_calibration_config()
        self.values = {item["name"]: 50.0 for item in self.cfg["indicators"]}

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self):
        return panel.altseason_panel(
            self.values, self.cfg, ledger_path=self.ledger, catalog_path=self.catalog
        )

    def _mutate_ledger(self, change):
        data = json.loads(self.ledger.read_text(encoding="utf-8"))
        change(data["learnings"])
        self.ledger.write_text(json.dumps(data), encoding="utf-8")

    def test_real_decision_records_applied_learning_and_refuses_unverified_scores(self):
        report = self._run()
        self.assertEqual(report["applied_learning_ids"], [panel.ALTSEASON_LEARNING_ID])
        self.assertEqual(report["decision_status"], "CALIBRATION_UNVERIFIED")
        self.assertFalse(report["historical_backtest_verified"])
        self.assertEqual(report["scored"], 0)
        self.assertEqual(report["composite_score"], "N/A")
        self.assertTrue(all(row["score"] == "N/A" for row in report["indicators"].values()))

    def test_positive_synthetic_calibration_does_not_claim_real_market_backtest(self):
        cfg = json.loads(json.dumps(self.cfg))
        for row in cfg["indicators"]:
            if row["name"] == "btc_dominance":
                row.update(validated=True, lo=40.0, hi=60.0)
        report = panel.altseason_panel(
            {"btc_dominance": 45.0}, cfg,
            ledger_path=self.ledger, catalog_path=self.catalog,
        )
        self.assertEqual(report["indicators"]["btc_dominance"]["score"], 75.0)
        self.assertEqual(report["composite_score"], "N/A")
        self.assertEqual(report["decision_status"], "CALIBRATION_UNVERIFIED")
        self.assertEqual(report["applied_learning_ids"], [panel.ALTSEASON_LEARNING_ID])

    def test_nonfinite_or_malformed_market_input_cannot_score(self):
        cfg = json.loads(json.dumps(self.cfg))
        target = next(row for row in cfg["indicators"] if row["name"] == "btc_dominance")
        target.update(validated=True, lo=40.0, hi=60.0)
        for invalid in (float("nan"), float("inf"), float("-inf"), "NaN", "Infinity", "not a number", True):
            with self.subTest(invalid=repr(invalid)):
                report = panel.altseason_panel(
                    {"btc_dominance": invalid}, cfg,
                    ledger_path=self.ledger, catalog_path=self.catalog,
                )
                row = report["indicators"]["btc_dominance"]
                self.assertIsNone(row["value"])
                self.assertEqual(row["score"], "N/A")
                self.assertEqual(report["composite_score"], "N/A")
                self.assertEqual(report["decision_status"], "CALIBRATION_UNVERIFIED")
                self.assertEqual(report["applied_learning_ids"], [panel.ALTSEASON_LEARNING_ID])
                json.dumps(report, allow_nan=False)

    def test_nonfinite_or_malformed_calibration_bounds_cannot_score(self):
        for lo, hi in ((float("nan"), 60.0), (40.0, float("inf")),
                       (float("-inf"), 60.0), ("bad", 60.0)):
            with self.subTest(lo=repr(lo), hi=repr(hi)):
                cfg = json.loads(json.dumps(self.cfg))
                target = next(row for row in cfg["indicators"] if row["name"] == "btc_dominance")
                target.update(validated=True, lo=lo, hi=hi)
                report = panel.altseason_panel(
                    {"btc_dominance": 45.0}, cfg,
                    ledger_path=self.ledger, catalog_path=self.catalog,
                )
                self.assertEqual(report["indicators"]["btc_dominance"]["score"], "N/A")
                self.assertEqual(report["decision_status"], "CALIBRATION_UNVERIFIED")

    def test_missing_learning_fails_closed(self):
        self._mutate_ledger(
            lambda rows: rows.__setitem__(
                slice(None), [row for row in rows
                              if row.get("learning_id") != panel.ALTSEASON_LEARNING_ID]
            )
        )
        with self.assertRaisesRegex(CatalogError, "bridge_failure"):
            self._run()

    def test_inactive_learning_fails_closed(self):
        def retire(rows):
            next(row for row in rows
                 if row.get("learning_id") == panel.ALTSEASON_LEARNING_ID)["status"] = "inactive"
        self._mutate_ledger(retire)
        with self.assertRaisesRegex(CatalogError, "bridge_failure"):
            self._run()

    def test_removed_finance_tag_fails_closed(self):
        def untag(rows):
            next(row for row in rows
                 if row.get("learning_id") == panel.ALTSEASON_LEARNING_ID)["plan_tags"] = ["system"]
        self._mutate_ledger(untag)
        with self.assertRaisesRegex(CatalogError, "bridge_failure"):
            self._run()

    def test_changed_decision_fails_closed(self):
        def replace_decision(rows):
            next(row for row in rows
                 if row.get("learning_id") == panel.ALTSEASON_LEARNING_ID)["decision"] = "Ignore calibration"
        self._mutate_ledger(replace_decision)
        with self.assertRaisesRegex(CatalogError, "bridge_failure"):
            self._run()

    def test_modified_claim_with_old_learning_id_fails_closed(self):
        def tamper(rows):
            row = next(row for row in rows
                       if row.get("learning_id") == panel.ALTSEASON_LEARNING_ID)
            row["claim"] += " [modified without recalculating learning_id]"
        self._mutate_ledger(tamper)
        with self.assertRaisesRegex(CatalogError, "unstable learning_id"):
            self._run()

    def test_modified_canonical_url_with_old_source_id_fails_closed(self):
        row = next(row for row in json.loads(self.ledger.read_text())["learnings"]
                   if row.get("learning_id") == panel.ALTSEASON_LEARNING_ID)
        target = row["source_ids"][0]
        data = json.loads(self.catalog.read_text(encoding="utf-8"))
        source = next(src for src in data["sources"] if src["source_id"] == target)
        source["canonical"] = "https://example.org/altered-policy-source"
        self.catalog.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(CatalogError, "unstable source_id"):
            self._run()

    def test_missing_source_reference_fails_closed(self):
        row = next(row for row in json.loads(self.ledger.read_text())["learnings"]
                   if row.get("learning_id") == panel.ALTSEASON_LEARNING_ID)
        source_to_remove = row["source_ids"][0]
        data = json.loads(self.catalog.read_text(encoding="utf-8"))
        data["sources"] = [source for source in data["sources"]
                           if source["source_id"] != source_to_remove]
        self.catalog.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaisesRegex(CatalogError, "bridge_failure"):
            self._run()


if __name__ == "__main__":
    unittest.main()
