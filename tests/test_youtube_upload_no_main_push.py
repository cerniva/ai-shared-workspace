"""YouTube upload workflow must not mutate main or discard upload evidence."""
import unittest
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "youtube-upload.yml"


class YouTubeUploadLedgerSafetyTests(unittest.TestCase):
    def test_no_main_write_or_push(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)
        self.assertNotIn("git push", text)
        self.assertNotIn("git pull", text)
        self.assertNotIn("git commit", text)
        self.assertNotIn("HEAD:main", text)

    def test_remote_upload_id_and_ledger_survive_as_review_artifact(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("scripts/shorts_lesson_48h.py record", text)
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("knowledge/shorts/upload_ledger.json", text)
        self.assertIn("${{ runner.temp }}/upload_result.json", text)
        self.assertIn("if-no-files-found: error", text)


if __name__ == "__main__":
    unittest.main()
