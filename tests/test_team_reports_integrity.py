import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEAM_REPORTS = ROOT / "messages" / "team-reports.md"


class TeamReportsIntegrityTests(unittest.TestCase):
    def test_team_reports_is_not_stubbed_or_truncated(self):
        text = TEAM_REPORTS.read_text(encoding="utf-8")
        self.assertNotIn("DO NOT USE STUB", text)
        self.assertIn("RPT-20260927-011600-chatgpt-collaboration-protocol", text)
        self.assertIn("RPT-20260927-215100-grok-meta-share-audit", text)
        self.assertGreaterEqual(text.count("\n## RPT-"), 10)


if __name__ == "__main__":
    unittest.main()
