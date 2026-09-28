import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".github" / "workflows" / "shorts-free-build.yml"
RENDER = ROOT / ".github" / "workflows" / "shorts-free-render.yml"


class ShortsFreeBuildWorkflowTests(unittest.TestCase):
    def _text(self):
        return BUILD.read_text(encoding="utf-8")

    def test_build_workflow_uses_both_provider_secrets_without_echoing_values(self):
        text = self._text()
        self.assertIn("PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}", text)
        self.assertIn("PIXABAY_API_KEY: ${{ secrets.PIXABAY_API_KEY }}", text)
        self.assertNotIn('echo "$PEXELS_API_KEY"', text)
        self.assertNotIn('echo "$PIXABAY_API_KEY"', text)

    def test_build_workflow_calls_free_pipeline_and_preflight(self):
        text = self._text()
        self.assertIn("scripts/shorts_free_pipeline.py", text)
        self.assertIn("scripts/shorts_preflight.py", text)
        self.assertIn("independent_review_missing", text)

    def test_build_workflow_uploads_mp4_preflight_and_provenance_artifacts(self):
        text = self._text()
        self.assertIn("actions/upload-artifact", text)
        self.assertIn("preflight.json", text)
        self.assertIn("provenance.json", text)
        self.assertIn("captions.srt", text)
        self.assertIn("render.json", text)
        self.assertIn("retention-days: 7", text)

    def test_build_workflow_never_publishes_or_calls_paid_generators(self):
        text = self._text().lower()
        for forbidden in ("youtube_upload.py", "metricool", "buffer", "heygen", "runway", "higgsfield", "openart", "elevenlabs"):
            self.assertNotIn(forbidden, text)

    def test_existing_secret_free_render_workflow_remains_secret_free(self):
        text = RENDER.read_text(encoding="utf-8")
        self.assertNotIn("secrets.", text)
        self.assertNotIn("PEXELS_API_KEY", text)
        self.assertNotIn("PIXABAY_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
