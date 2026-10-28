"""YouTube upload workflow must not mutate main or discard upload evidence."""
import unittest
import hashlib
import tempfile
from pathlib import Path
from scripts.verify_shorts_upload_evidence import verify

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
        self.assertIn("verify_shorts_upload_evidence.py", text)
        self.assertIn("shorts-upload-evidence/", text)
        self.assertIn("if-no-files-found: error", text)

    def test_upload_attempts_are_serialized_without_cancelling_receipts(self):
        """Avoid overlapping inserts; cross-run replay remains separately blocked."""
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "concurrency:\n  group: shorts-upload-${{ github.repository }}\n  cancel-in-progress: false",
            text,
        )
        self.assertNotIn("cancel-in-progress: true", text)

    def test_artifact_digest_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            files = {"upload_ledger.json": b"ledger", "upload_result.json": b"remote-id"}
            for name, contents in files.items():
                (folder / name).write_bytes(contents)
            (folder / "SHA256SUMS").write_text("".join(
                hashlib.sha256(value).hexdigest() + "  " + name + "\n"
                for name, value in files.items()
            ), encoding="utf-8")
            verify(folder)
            (folder / "upload_result.json").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                verify(folder)


if __name__ == "__main__":
    unittest.main()
