import unittest

from scripts.research_router import ResearchRequest, route_research


class ResearchRouterTests(unittest.TestCase):
    def test_fresh_public_defaults_to_web(self):
        plan = route_research(ResearchRequest(query="latest AI news", fresh=True))
        self.assertEqual(plan.primary, "web_search")

    def test_deep_discovery_prefers_exa(self):
        plan = route_research(ResearchRequest(query="find related technical papers", deep=True))
        self.assertEqual(plan.primary, "exa")

    def test_page_extraction_prefers_firecrawl(self):
        plan = route_research(ResearchRequest(query="extract this JS-heavy page", extract=True))
        self.assertEqual(plan.primary, "firecrawl")

    def test_interactive_action_uses_browser_worker(self):
        plan = route_research(ResearchRequest(query="log in and click publish", interactive=True))
        self.assertEqual(plan.primary, "browser_worker")

    def test_high_impact_requires_cross_check(self):
        plan = route_research(ResearchRequest(query="payment compliance change", fresh=True, domain="payments"))
        self.assertTrue(plan.cross_check)
        self.assertGreaterEqual(plan.min_sources, 2)

    def test_missing_provider_falls_back(self):
        plan = route_research(ResearchRequest(query="deep market discovery", deep=True), available={"exa": False, "web_search": True})
        self.assertEqual(plan.primary, "web_search")
        self.assertIn("exa_unavailable", plan.notes)


if __name__ == "__main__":
    unittest.main()
