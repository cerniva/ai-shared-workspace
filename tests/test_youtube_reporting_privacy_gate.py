"""Tests for the opt-in Reporting API privacy-gate consumer.

Uses the canonical ledger/catalog read-only, plus temp copies for fail-closed cases.
No channel data, no network, PayoutLens out of scope.
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, DEFAULT_CATALOG
from scripts.learning_bridge import DEFAULT_LEDGER
from scripts import youtube_reporting_privacy_gate as gate


HEADER = "day,country,ageGroup,views\n"


class PrivacyGateRuleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.ledger = self.tmp / "learning_ledger.json"
        self.catalog = self.tmp / "source_catalog.json"
        shutil.copy(DEFAULT_LEDGER, self.ledger)
        shutil.copy(DEFAULT_CATALOG, self.catalog)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _mutate_learning(self, **changes):
        data = json.loads(self.ledger.read_text(encoding="utf-8"))
        for item in data["learnings"]:
            if item.get("learning_id") == gate.LEARNING_ID:
                item.update(changes)
        self.ledger.write_text(json.dumps(data), encoding="utf-8")

    def test_canonical_rule_is_readable(self):
        evidence = gate.read_rule()
        self.assertEqual(evidence["learning_id"], "learn_607a11f5b569ffa0")
        self.assertEqual(evidence["gate"], "REPORT_PRIVACY_SUPPRESSION_GATE")

    def test_missing_learning_fails_closed(self):
        data = json.loads(self.ledger.read_text(encoding="utf-8"))
        data["learnings"] = [i for i in data["learnings"] if i.get("learning_id") != gate.LEARNING_ID]
        self.ledger.write_text(json.dumps(data), encoding="utf-8")
        with self.assertRaises(CatalogError):
            gate.read_rule(self.ledger, self.catalog)

    def test_unverified_evidence_fails_closed(self):
        self._mutate_learning(evidence_status="candidate")
        with self.assertRaises(CatalogError):
            gate.read_rule(self.ledger, self.catalog)

    def test_source_mismatch_fails_closed(self):
        self._mutate_learning(source_ids=["src_0000000000000000"])
        with self.assertRaises(CatalogError):
            gate.read_rule(self.ledger, self.catalog)

    def test_rule_checked_before_csv_parsing(self):
        self._mutate_learning(evidence_status="candidate")
        with self.assertRaises(CatalogError):
            gate.summarize_csv("", self.ledger, self.catalog)


class PrivacyGateCsvTests(unittest.TestCase):
    def test_suppressed_rows_counted_not_dropped(self):
        csv_text = HEADER + "20261001,TR,age25-34,10\n20261001,ZZ,age25-34,4\n20261001,US,NULL,6\n"
        result = gate.summarize_csv(csv_text)
        self.assertEqual(result["status"], "VALID_DATA")
        self.assertEqual(result["rows"], 3)
        self.assertEqual(result["total_views"], 20)
        self.assertEqual(result["privacy_suppressed_rows"], 2)
        self.assertEqual(result["privacy_suppressed_views"], 10)
        self.assertFalse(result["production_channel_access"])

    def test_reporting_api_snake_case_columns_detected(self):
        # Real Reporting API CSV headers (channel_basic_a3 / channel_traffic_source_a3
        # / channel_province_a3 / channel_demographics_a1) are snake_case.
        header = (
            "date,channel_id,video_id,live_or_on_demand,subscribed_status,"
            "country_code,province_code,traffic_source_detail,age_group,gender,views\n"
        )
        rows = (
            "20261001,c,v,on_demand,subscribed,TR,,ext,AGE_25_34,FEMALE,10\n"
            "20261001,c,v,on_demand,subscribed,ZZ,,ext,AGE_25_34,FEMALE,4\n"
            "20261001,c,v,on_demand,subscribed,US,US-ZZ,ext,AGE_25_34,FEMALE,3\n"
            "20261001,c,v,on_demand,subscribed,US,US-TX,NULL,AGE_25_34,FEMALE,2\n"
            "20261001,c,v,on_demand,NULL,US,US-TX,ext,AGE_25_34,FEMALE,1\n"
            "20261001,c,v,on_demand,subscribed,US,US-TX,ext,NULL,NULL,5\n"
        )
        result = gate.summarize_csv(header + rows)
        self.assertEqual(result["rows"], 6)
        self.assertEqual(result["total_views"], 25)
        self.assertEqual(result["privacy_suppressed_rows"], 5)
        self.assertEqual(result["privacy_suppressed_views"], 15)

    def test_snake_case_unsuppressed_values_not_flagged(self):
        header = "date,country_code,age_group,views\n"
        result = gate.summarize_csv(header + "20261001,TR,AGE_25_34,7\n20261001,DE,AGE_18_24,3\n")
        self.assertEqual(result["total_views"], 10)
        self.assertEqual(result["privacy_suppressed_rows"], 0)
        self.assertEqual(result["privacy_suppressed_views"], 0)

    def test_header_only_is_valid_no_data(self):
        result = gate.summarize_csv(HEADER)
        self.assertEqual(result["status"], "VALID_NO_DATA")
        self.assertEqual(result["total_views"], 0)

    def test_empty_file_rejected(self):
        with self.assertRaisesRegex(ValueError, "INVALID_EMPTY_FILE"):
            gate.summarize_csv("  \n")

    def test_bad_headers_rejected(self):
        for text in ("day,views,views\n1,2,3\n", "day,country\n1,TR\n", "day, views\n1,2\n"):
            with self.subTest(text=text):
                with self.assertRaisesRegex(ValueError, "INVALID_HEADER"):
                    gate.summarize_csv(text)

    def test_ragged_rows_rejected(self):
        for row in ("20261001,TR,age25-34,1,extra\n", "20261001,TR\n"):
            with self.subTest(row=row):
                with self.assertRaisesRegex(ValueError, "INVALID_ROW_WIDTH"):
                    gate.summarize_csv(HEADER + row)

    def test_non_integer_views_rejected(self):
        for value in ("-1", "1.5", "", "١٢"):
            with self.subTest(value=value):
                with self.assertRaisesRegex(ValueError, "INVALID_VIEWS"):
                    gate.summarize_csv(HEADER + f"20261001,TR,age25-34,{value}\n")


if __name__ == "__main__":
    unittest.main()
