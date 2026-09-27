import unittest
from scripts.research_router import ResearchRequest, route_research

class ResearchRouterTests(unittest.TestCase):
    def test_fresh_public_defaults_to_web(self):
        plan = route_research(ResearchRequest(query="latest AI news", fresh=True))
        self.assertEqual(plan.primary, "web_search")

if __name__ == "__main__":
    unittest.main()
