import unittest

from orchestrator.models import Job, Provider
from orchestrator.router import route_job
from research_worker.providers import ResearchProvider
from research_worker.worker import ResearchWorker
from shorts_worker.worker import ShortsWorker
from shopify_worker.worker import ShopifyWorker


class ApiFirstIntegrationTests(unittest.TestCase):
    def test_research_to_shorts_draft_flow(self):
        research = ResearchWorker([ResearchProvider(name="exa", available=True, priority=10)]).research("bitcoin history", "shorts")
        self.assertEqual(research.status, "ready")
        draft = ShortsWorker(youtube_api_available=True).draft("bitcoin history", research.provider)
        self.assertEqual(draft.status, "ready")
        self.assertEqual(draft.metadata["research_provider"], "exa")

    def test_orchestrator_prefers_api_for_shopify_read(self):
        routed = route_job(Job(kind="shopify", action="catalog_read", allow_browser_fallback=True), [Provider("browser", "browser", True), Provider("shopify_admin_api", "api", True)])
        self.assertEqual(routed.provider, "shopify_admin_api")
        result = ShopifyWorker(admin_api_available=True, browser_available=True).catalog_read("sku-1", allow_browser_fallback=True)
        self.assertEqual(result.provider, "shopify_admin_api")

    def test_irreversible_actions_remain_gated(self):
        shorts = ShortsWorker(youtube_api_available=True).publish("video.mp4", approved=False)
        shopify = ShopifyWorker(admin_api_available=True).catalog_write({"title": "Product"}, approved=False)
        self.assertEqual(shorts.status, "approval_required")
        self.assertEqual(shopify.status, "approval_required")

    def test_missing_services_fail_closed(self):
        research = ResearchWorker([ResearchProvider(name="exa", available=False)]).research("query", "research")
        shorts = ShortsWorker(youtube_api_available=False).analytics("video")
        shopify = ShopifyWorker(admin_api_available=False).catalog_read("sku")
        self.assertEqual(research.status, "blocked")
        self.assertEqual(shorts.status, "blocked")
        self.assertEqual(shopify.status, "blocked")


if __name__ == "__main__":
    unittest.main()
