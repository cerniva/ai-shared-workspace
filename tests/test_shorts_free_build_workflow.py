import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_WORKFLOW = ROOT / ".github" / "workflows" / "shorts-free-build.yml"
RENDER_WORKFLOW = ROOT / ".github" / "workflows" / "shorts-free-render.yml"


class ShortsFreeBuildWorkflowTests(unittest.TestCase):
    def test_build_workflow_uses_both_provider_secrets_without_echoing_values(self):
        """Provider credentials must enter only through secret-backed environment variables."""
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("PEXELS_API_KEY: ${{ secrets.PEXELS_API_KEY }}", text)
        self.assertIn("PIXABAY_API_KEY: ${{ secrets.PIXABAY_API_KEY }}", text)
        self.assertNotIn("echo $PEXELS_API_KEY", text)
        self.assertNotIn("echo $PIXABAY_API_KEY", text)

    def test_build_workflow_calls_free_pipeline_and_preflight(self):
        """The build must use the free orchestrator and existing technical preflight."""
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("scripts/shorts_free_pipeline.py", text)
        self.assertIn("scripts/shorts_preflight.py", text)
        self.assertIn("independent_review_missing", text)

    def test_build_workflow_uploads_mp4_preflight_and_provenance_artifacts(self):
        """A successful build must preserve the render and its audit files."""
        text = BUILD_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("actions/upload-artifact@v4", text)
        self.assertIn("artifacts/preflight.json", text)
        self.assertIn("artifacts/bundle/provenance.json", text)
        self.assertIn("artifacts/bundle/captions.srt", text)
        self.assertIn("artifacts/bundle/render.json", text)
        self.assertIn("artifacts/$OUTPUT_NAME", text)

    def test_build_workflow_never_publishes_or_calls_paid_generators(self):
        """The acquisition workflow is production-only and never publishes or spends paid credits."""
        text = BUILD_WORKFLOW.read_text(encoding="utf-8").lower()
        for forbidden in (
            "youtube_upload.py",
            "metricool",
            "buffer",
            "openart",
            "runway",
            "heygen",
            "elevenlabs",
        ):
            self.assertNotIn(forbidden, text)

    def test_existing_secret_free_render_workflow_remains_secret_free(self):
        """The older local-only renderer must stay usable without provider credentials."""
        text = RENDER_WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("secrets.", text)
        self.assertNotIn("PEXELS_API_KEY", text)
        self.assertNotIn("PIXABAY_API_KEY", text)


if __name__ == "__main__":
    unittest.main()
