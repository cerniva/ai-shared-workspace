"""Guard the existing 25 Oct CMC denominator promotion without importing it.

This test never changes the canonical catalog, learning ledger, or PayoutLens.
"""
import json
import unittest
from pathlib import Path

from scripts.knowledge_bridge import canonicalize, source_id


PROMOTION = (
    Path(__file__).resolve().parents[1]
    / "knowledge/promotions/2026-10-25-finance-cmc-volume-denominator-gate.json"
)
OFFICIAL = "https://coinmarketcap.com/api/documentation/pro-api-reference/global-metrics"


def validate_promotion(document):
    if document.get("schema_version") != 1:
        raise ValueError("schema_version must be 1")
    sources = document.get("sources")
    learnings = document.get("learnings")
    if not isinstance(sources, list) or not isinstance(learnings, list):
        raise ValueError("sources and learnings must be lists")
    ids, canonicals = set(), set()
    for item in sources:
        canonical = canonicalize(item["canonical"])
        sid = source_id(canonical)
        if item["source_id"] != sid or sid in ids or canonical in canonicals:
            raise ValueError("invalid or duplicate canonical source")
        ids.add(sid)
        canonicals.add(canonical)
    learning_ids = set()
    for item in learnings:
        lid = item["learning_id"]
        if lid in learning_ids or not item.get("source_ids"):
            raise ValueError("duplicate learning or missing source refs")
        learning_ids.add(lid)
        if not set(item["source_ids"]) <= ids:
            raise ValueError("orphan source reference")
    return ids, canonicals


class CMCDenominatorPromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(PROMOTION.read_text(encoding="utf-8"))

    def test_schema_canonical_dedup_and_references(self):
        ids, urls = validate_promotion(self.doc)
        self.assertEqual(len(ids), 3)
        self.assertEqual(len(self.doc["learnings"]), 1)
        self.assertIn(OFFICIAL, urls)
        self.assertIn(source_id(OFFICIAL), self.doc["learnings"][0]["source_ids"])

    def test_negative_orphan_source_fails_closed(self):
        bad = json.loads(json.dumps(self.doc))
        bad["learnings"][0]["source_ids"].append("src_missing")
        with self.assertRaisesRegex(ValueError, "orphan"):
            validate_promotion(bad)

    def test_negative_duplicate_and_changed_identity_fail_closed(self):
        bad = json.loads(json.dumps(self.doc))
        bad["sources"].append(dict(bad["sources"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_promotion(bad)
        bad = json.loads(json.dumps(self.doc))
        bad["sources"][0]["canonical"] += "?utm_source=wrong"
        bad["sources"][0]["source_id"] = "src_wrong"
        with self.assertRaisesRegex(ValueError, "invalid"):
            validate_promotion(bad)


if __name__ == "__main__":
    unittest.main()
