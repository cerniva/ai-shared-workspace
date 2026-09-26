import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.grok_senses import blocked_next_action


class GrokBlockerGuidanceTests(unittest.TestCase):
    def test_403_reports_team_permission_or_blocked_status_without_key(self):
        guidance = blocked_next_action(RuntimeError("provider HTTP 403"))
        self.assertIn("permission", guidance)
        self.assertIn("blocked", guidance)
        self.assertIn("never paste", guidance)

    def test_401_guidance_never_requests_key_value(self):
        guidance = blocked_next_action(RuntimeError("provider HTTP 401"))
        self.assertIn("XAI_API_KEY", guidance)
        self.assertIn("never paste", guidance)

    def test_404_guidance_checks_endpoint_and_model(self):
        guidance = blocked_next_action(RuntimeError("provider HTTP 404"))
        self.assertIn("endpoint and model", guidance)

    def test_unknown_failure_does_not_recommend_blind_retry(self):
        guidance = blocked_next_action(RuntimeError("provider HTTP 502"))
        self.assertIn("do not retry unchanged", guidance)


if __name__ == "__main__":
    unittest.main()
