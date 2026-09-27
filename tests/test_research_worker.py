import unittest

from research_worker.worker import ResearchWorker
from research_worker.providers import ResearchProvider


class ResearchWorkerTests(unittest.TestCase):
    def test_prefers_available_primary_search_provider(self):
        providers = [
            ResearchProvider(name="exa", available=True, priority=10),
            ResearchProvider(name="tavily", available=True, priority=20),
        ]
        result = ResearchWorker(providers).research("viral products", "shopify")
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.provider, "exa")
        self.assertEqual(result.metadata["query"], "viral products")
        self.assertEqual(result.metadata["purpose"], "shopify")

    def test_falls_back_to_next_available_provider(self):
        providers = [
            ResearchProvider(name="exa", available=False, priority=10),
            ResearchProvider(name="tavily", available=True, priority=20),
        ]
        result = ResearchWorker(providers).research("shorts trends", "shorts")
        self.assertEqual(result.status, "degraded")
        self.assertEqual(result.provider, "tavily")
        self.assertTrue(result.fallback_reason)

    def test_missing_credentials_fail_closed(self):
        providers = [ResearchProvider(name="exa", available=False, priority=10)]
        result = ResearchWorker(providers).research("query", "research")
        self.assertEqual(result.status, "blocked")
        self.assertIsNone(result.provider)

    def test_result_records_evidence_metadata(self):
        provider = ResearchProvider(name="exa", available=True, priority=10)
        result = ResearchWorker([provider]).research("query", "research")
        self.assertIn("timestamp", result.metadata)
        self.assertEqual(result.metadata["source_provider"], "exa")


if __name__ == "__main__":
    unittest.main()
