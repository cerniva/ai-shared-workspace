"""Remote videos.insert receipt survives a failed read-back (no network/credentials)."""
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts import youtube_upload


class YouTubeUploadReceiptTests(unittest.TestCase):
    def _fake_modules(self, youtube):
        pkg = types.ModuleType("googleapiclient")
        pkg.__path__ = []
        discovery = types.ModuleType("googleapiclient.discovery")
        discovery.build = lambda *args, **kwargs: youtube
        errors = types.ModuleType("googleapiclient.errors")
        errors.HttpError = type("HttpError", (Exception,), {})
        http = types.ModuleType("googleapiclient.http")
        http.MediaFileUpload = lambda *args, **kwargs: object()
        return {
            "googleapiclient": pkg,
            "googleapiclient.discovery": discovery,
            "googleapiclient.errors": errors,
            "googleapiclient.http": http,
        }

    def _mock_youtube(self):
        youtube = MagicMock()
        youtube.channels().list().execute.return_value = {
            "items": [{"id": youtube_upload.CHANNEL_ID}]
        }
        youtube.videos().insert().next_chunk.return_value = (None, {"id": "remote-123"})
        return youtube

    def test_failed_readback_preserves_id_sha_and_unverified_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "clip.mp4"
            video.write_bytes(b"licensed-video-placeholder")
            receipt = Path(tmp) / "receipt" / "remote.json"
            youtube = self._mock_youtube()
            youtube.videos().list().execute.side_effect = RuntimeError("readback unavailable")
            with patch.dict(sys.modules, self._fake_modules(youtube)):
                with patch.object(youtube_upload, "credentials_from_env", return_value=object()):
                    with self.assertRaisesRegex(RuntimeError, "readback unavailable"):
                        youtube_upload.upload(video, {"title": "Test", "description": "Test"},
                                              False, False, False, receipt)
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(saved["video_id"], "remote-123")
            self.assertEqual(saved["source_sha256"], youtube_upload.sha256_file(video))
            self.assertEqual(saved["requested_privacy_status"], "private")
            self.assertIs(saved["read_back_verified"], False)
            self.assertFalse(receipt.with_name(receipt.name + ".tmp").exists())

    def test_successful_readback_marks_receipt_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "clip.mp4"
            video.write_bytes(b"licensed-video-placeholder")
            receipt = Path(tmp) / "receipt.json"
            youtube = self._mock_youtube()
            youtube.videos().list().execute.return_value = {
                "items": [{"snippet": {"channelId": youtube_upload.CHANNEL_ID},
                           "status": {"privacyStatus": "private"}}]
            }
            with patch.dict(sys.modules, self._fake_modules(youtube)):
                with patch.object(youtube_upload, "credentials_from_env", return_value=object()):
                    result = youtube_upload.upload(video, {"title": "Test", "description": "Test"},
                                                   False, False, False, receipt)
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(result["video_id"], "remote-123")
            self.assertIs(saved["read_back_verified"], True)
            self.assertEqual(saved["actual_privacy_status"], "private")


if __name__ == "__main__":
    unittest.main()
