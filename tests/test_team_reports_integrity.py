import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEAM_REPORTS = ROOT / "messages" / "team-reports.md"
TEAM_REPORTS_ARCHIVE = ROOT / "messages" / "team-reports-archive-20260927.md"


class TeamReportsIntegrityTests(unittest.TestCase):
    def test_team_reports_history_is_preserved_and_active_stream_is_readable(self):
        current = TEAM_REPORTS.read_text(encoding="utf-8")
        archive = TEAM_REPORTS_ARCHIVE.read_text(encoding="utf-8")

        self.assertNotIn("DO NOT USE STUB", current)
        self.assertIn("team-reports-archive-20260927.md", current)
        self.assertIn("RPT-20260927-215100-grok-meta-share-audit", current)
        self.assertIn("RPT-20260927-011600-chatgpt-collaboration-protocol", archive)
        self.assertGreaterEqual(
            current.count("\n## RPT-") + archive.count("\n## RPT-"),
            10,
        )


if __name__ == "__main__":
    unittest.main()
