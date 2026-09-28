from __future__ import annotations

import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from scripts.knowledge_bridge import CatalogError, SourceCatalog, canonicalize, source_id


def record(canonical: str, name: str = "Python docs") -> dict[str, str]:
    return {
        "source_name": name,
        "canonical": canonical,
        "category": "concurrency",
        "purpose": "Safe local source-catalog writes",
        "evidence_tier": "official",
        "access_status": "verified-public",
        "cost_quota": "free",
        "reliability_limits": "Unix only",
        "discovered_at": "2026-09-28T00:59:00+00:00",
        "provenance": "verified",
        "last_successful_use": "2026-09-28T00:59:00+00:00",
    }


class KnowledgeBridgeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "source_catalog.json"
        self.catalog = SourceCatalog(self.path)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_canonicalize_removes_tracking_and_fragment(self) -> None:
        value = canonicalize("HTTPS://Docs.Python.org:443/3/library/fcntl.html/?utm_source=x#flock")
        self.assertEqual(value, "https://docs.python.org/3/library/fcntl.html")

    def test_stable_id(self) -> None:
        canonical = "https://docs.python.org/3/library/fcntl.html"
        self.assertEqual(source_id(canonical), source_id(canonical))
        self.assertTrue(source_id(canonical).startswith("src_"))

    def test_add_is_idempotent_and_read_back_matches(self) -> None:
        first, created = self.catalog.add(record("https://docs.python.org/3/library/fcntl.html"))
        second, created_again = self.catalog.add(record("https://docs.python.org/3/library/fcntl.html?utm_source=test"))
        self.assertTrue(created)
        self.assertFalse(created_again)
        self.assertEqual(first, second)
        self.assertEqual(self.catalog.find(first["source_id"]), first)
        self.assertEqual(self.catalog.validate(), 1)

    def test_rejects_secret_query_parameter(self) -> None:
        with self.assertRaises(CatalogError):
            self.catalog.add(record("https://example.com/docs?api_key=secret-value"))

    def test_rejects_email_and_secret_like_value(self) -> None:
        unsafe = record("https://example.com/docs")
        unsafe["purpose"] = "Contact personal@example.com"
        with self.assertRaises(CatalogError):
            self.catalog.add(unsafe)
        unsafe = record("https://example.com/docs")
        unsafe["failure_note"] = "Bearer abcdefghijklmnopqrstuvwxyz"
        with self.assertRaises(CatalogError):
            self.catalog.add(unsafe)

    def test_concurrent_duplicate_writes_create_one_record(self) -> None:
        payload = record("https://docs.python.org/3/library/fcntl.html")
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: self.catalog.add(payload), range(24)))
        self.assertEqual(sum(1 for _, created in results if created), 1)
        self.assertEqual(len(self.catalog.list()), 1)
        parsed = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(len(parsed["sources"]), 1)


if __name__ == "__main__":
    unittest.main()
