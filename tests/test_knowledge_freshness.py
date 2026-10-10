import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from scripts import knowledge_freshness as kf
from scripts.knowledge_bridge import CatalogError, SourceCatalog, canonicalize, source_id
from scripts.knowledge_promote import apply_promotions

NOW = datetime(2026, 10, 10, tzinfo=timezone.utc)


def src(url, last):
    c = canonicalize(url)
    return {"source_id": source_id(c), "canonical": c, "source_name": "n", "category": "c", "purpose": "p",
            "evidence_tier": "official", "access_status": "verified-public", "cost_quota": "free",
            "reliability_limits": "r", "discovered_at": "2026-08-01T00:00:00+00:00", "provenance": "verified",
            "last_successful_use": last, "failure_note": None}


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "knowledge" / "promotions").mkdir(parents=True)
        self.old = src("https://old.example/a", "2026-08-01T00:00:00+00:00")
        self.dead = src("https://dead.example/b", None)
        self.fresh = src("https://new.example/c", "2026-10-05T00:00:00+00:00")
        self.cat = self.root / "knowledge" / "source_catalog.json"
        self.cat.write_text(json.dumps({"schema_version": 1, "updated_at": None,
                                        "sources": sorted([self.old, self.dead, self.fresh], key=lambda r: r["source_id"])}))
        self.led = self.root / "knowledge" / "learning_ledger.json"
        self.led.write_text(json.dumps({"schema_version": 1, "learnings": []}))

    def tearDown(self):
        self.tmp.cleanup()

    def fetch(self, url):
        return 200 if "old" in url else 404

    def test_lists_only_stale(self):
        rep = kf.run(catalog=self.cat, ledger=self.led, promotions=self.root / "knowledge" / "promotions", now=NOW)
        ids = {r["source_id"] for r in rep["stale_sources"]}
        self.assertEqual(ids, {self.old["source_id"], self.dead["source_id"]})  # dead falls back to discovered_at
        self.assertNotIn("refreshed", rep)

    def test_reverify_stages_promotion_and_promote_applies_it(self):
        before = self.cat.read_text()
        rep = kf.run(catalog=self.cat, ledger=self.led, promotions=self.root / "knowledge" / "promotions",
                     do_reverify=True, fetch=self.fetch, now=NOW)
        self.assertEqual(rep["refreshed"], [self.old["source_id"]])
        self.assertEqual(rep["failed"][0]["status"], 404)
        self.assertEqual(self.cat.read_text(), before)  # script never writes canonical files
        promo = json.loads(next((self.root / "knowledge" / "promotions").glob("freshness-*.json")).read_text())
        self.assertEqual(promo["schema_version"], 1)
        out = apply_promotions(self.root)
        self.assertEqual(out["sources_refreshed"], [self.old["source_id"]])
        row = SourceCatalog(self.cat).find(self.old["source_id"])
        self.assertEqual(row["last_successful_use"], "2026-10-10T00:00:00+00:00")
        # replay is a no-op
        self.assertNotIn("sources_refreshed", apply_promotions(self.root))

    def test_refresh_unknown_id_fails_closed(self):
        with self.assertRaises(CatalogError):
            kf.refresh_source(SourceCatalog(self.cat), "src_0000000000000000", "2026-10-10T00:00:00+00:00")

    def test_refresh_never_moves_backwards(self):
        self.assertFalse(kf.refresh_source(SourceCatalog(self.cat), self.fresh["source_id"], "2026-09-01T00:00:00+00:00"))

    def test_malformed_refresh_rejected(self):
        (self.root / "knowledge" / "promotions" / "x.json").write_text(
            json.dumps({"schema_version": 1, "source_refreshes": [{"source_id": "bad"}]}))
        with self.assertRaises(CatalogError):
            apply_promotions(self.root)


if __name__ == "__main__":
    unittest.main()
