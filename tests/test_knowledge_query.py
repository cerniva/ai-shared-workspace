import json
import tempfile
import unittest
from pathlib import Path

from scripts import knowledge_query as kq
from scripts import telegram_bot as tb

LEDGER = {"schema_version": 1, "learnings": [
    {"learning_id": "learn_a", "title": "Gumroad draft first", "domain": "gumroad-api",
     "claim": "POST products publishes unless draft=true", "decision": "send draft", "next_measurement": "x",
     "plan_tags": ["video_shopify"], "source_ids": ["src_g"], "evidence_status": "verified", "provenance": "verified",
     "outcome": "pending"},
    {"learning_id": "learn_b", "title": "Fed faiz kararı", "domain": "finance-news",
     "claim": "FOMC minutes released", "decision": "review", "next_measurement": "y",
     "plan_tags": ["finance"], "source_ids": ["src_f"], "evidence_status": "unverified", "provenance": "unverified",
     "outcome": "pending"},
]}
CATALOG = {"schema_version": 1, "sources": [
    {"source_id": "src_g", "source_name": "Gumroad API", "canonical": "https://gumroad.com/api",
     "category": "gumroad-api", "purpose": "products draft", "reliability_limits": "", "evidence_tier": "official",
     "provenance": "verified"},
    {"source_id": "src_f", "source_name": "Fed RSS", "canonical": "https://www.federalreserve.gov/feeds/press_all.xml",
     "category": "finance-news", "purpose": "press releases", "reliability_limits": "", "evidence_tier": "primary",
     "provenance": "verified"},
]}


class KnowledgeQueryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.ledger, self.catalog = d / "l.json", d / "c.json"
        self.ledger.write_text(json.dumps(LEDGER))
        self.catalog.write_text(json.dumps(CATALOG))

    def tearDown(self):
        self.tmp.cleanup()

    def q(self, *a, **k):
        return kq.query_knowledge(*a, ledger_path=self.ledger, catalog_path=self.catalog, **k)

    def test_free_text_ranks_both_kinds(self):
        ids = [h["id"] for h in self.q("gumroad draft")]
        self.assertEqual(set(ids), {"learn_a", "src_g"})

    def test_all_terms_required(self):
        self.assertEqual(self.q("gumroad fomc"), [])

    def test_turkish_folding(self):
        self.assertEqual([h["id"] for h in self.q("FAIZ KARARI", kind="learning")], ["learn_b"])

    def test_topic_plan_tag_filters(self):
        self.assertEqual({h["id"] for h in self.q(topic="finance")}, {"learn_b", "src_f"})
        self.assertEqual({h["id"] for h in self.q(plan="video_shopify")}, {"learn_a", "src_g"})
        self.assertEqual({h["id"] for h in self.q(tag="unverified")}, {"learn_b"})
        self.assertEqual({h["id"] for h in self.q(tag="official")}, {"src_g"})

    def test_limit_and_bad_kind(self):
        self.assertEqual(len(self.q(limit=1)), 1)
        with self.assertRaises(ValueError):
            self.q(kind="nope")

    def test_cli_json(self):
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            kq.main(["fed", "--json", "--ledger", str(self.ledger), "--catalog", str(self.catalog)])
        self.assertIn("src_f", buf.getvalue())

    def test_real_library_loads(self):
        self.assertIsInstance(kq.query_knowledge("youtube", limit=3), list)


class BilgiCommandTests(unittest.TestCase):
    def test_bilgi_routes_to_query(self):
        seen = {}

        def fake(question, limit=5):
            seen["q"] = question
            return [{"kind": "source", "id": "src_x", "title": "T", "score": 1, "url": "https://e", "snippet": "s"}]

        out = tb.knowledge_answer("gumroad taslak", query=fake)
        self.assertEqual(seen["q"], "gumroad taslak")
        self.assertIn("src_x", out)

    def test_bilgi_handler_usage_and_live(self):
        self.assertIn("Kullanım: /bilgi", tb.handle_text("/bilgi"))
        out = tb.handle_text("/bilgi gumroad")
        self.assertTrue(out)
        self.assertNotIn("Bilinmeyen komut", out)
        self.assertIn("/bilgi", tb.handle_text("/yardim"))


if __name__ == "__main__":
    unittest.main()
