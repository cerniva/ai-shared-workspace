import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "shorts-free-render.yml"


class ShortsFreeRenderWorkflowTests(unittest.TestCase):
    def test_manual_credit_free_render_workflow_is_fail_closed_for_publishing(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", text)
        self.assertIn("scripts/shorts_render.py", text)
        self.assertIn("scripts/shorts_preflight.py", text)
        self.assertIn("espeak-ng", text)
        self.assertIn("actions/upload-artifact", text)
        self.assertNotIn("youtube_upload.py", text)
        self.assertNotIn("secrets.", text)
        self.assertNotIn("OPENART", text.upper())
        self.assertNotIn("RUNWAY", text.upper())


if __name__ == "__main__":
    unittest.main()
