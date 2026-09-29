import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "youtube-upload.yml"


class YouTubeUploadWorkflowTests(unittest.TestCase):
    def test_render_artifact_handoff_is_opt_in_and_fail_closed(self):
        """Allow a prior free-render artifact without weakening upload safety defaults."""
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("source_mode:", text)
        self.assertIn("render_artifact", text)
        self.assertIn("render_run_id", text)
        self.assertIn("actions: read", text)
        self.assertIn("actions/download-artifact@v4", text)
        self.assertIn("run-id: ${{ inputs.render_run_id }}", text)
        self.assertIn("github-token: ${{ github.token }}", text)
        self.assertIn("render_run_id must be a positive numeric GitHub Actions run ID", text)
        self.assertIn("rendered_video_name must be a visible simple .mp4 filename", text)
        self.assertIn("default: false", text)
        self.assertIn('if [[ "$PUBLISH_PUBLICLY" == "true" ]]', text)
        self.assertIn("scripts/youtube_upload.py", text)
        self.assertIn("preflight_path:", text)
        self.assertIn("preflight_path must be empty when source_mode=render_artifact", text)
        self.assertIn('preflight="downloaded-render/preflight.json"', text)
        self.assertIn('python scripts/youtube_upload.py "$VIDEO_PATH" "$METADATA_PATH" --preflight "$PREFLIGHT_PATH"', text)
        self.assertNotIn('--preflight "$PREFLIGHT_PATH" --preflight "$PREFLIGHT_PATH"', text)

    def test_resolve_upload_video_has_one_source_mode_env_entry(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        section = text.split("- name: Resolve upload video", 1)[1].split("- name:", 1)[0]
        self.assertEqual(section.count("SOURCE_MODE: ${{ inputs.source_mode }}"), 1)

    def test_repo_mode_still_requires_existing_repo_relative_mp4_and_metadata(self):
        """Preserve the original repo-file upload path with traversal checks."""
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('repo_file(os.environ["METADATA_PATH"], "metadata_path", ".json")', text)
        self.assertIn('repo_file(os.environ["VIDEO_PATH_INPUT"], "video_path", ".mp4")', text)
        self.assertIn('path.is_absolute() or ".." in path.parts', text)
        self.assertIn("Missing GitHub Actions secret", text)
        self.assertIn('repo_file(preflight, "preflight_path", ".json")', text)


if __name__ == "__main__":
    unittest.main()
