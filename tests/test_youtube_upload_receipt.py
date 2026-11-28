"""Remote videos.insert receipt survives a failed read-back (no network/credentials)."""
import io
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
            self.assertEqual(saved["upload_state"], "REMOTE_ID_RECEIVED")
            self.assertEqual(saved["source_sha256"], youtube_upload.sha256_file(video))
            self.assertEqual(saved["requested_privacy_status"], "private")
            self.assertIs(saved["read_back_verified"], False)
            self.assertFalse(receipt.with_name(receipt.name + ".tmp").exists())

    def test_network_failure_before_video_id_preserves_ambiguous_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "clip.mp4"
            video.write_bytes(b"source-bytes")
            receipt = Path(tmp) / "receipt.json"
            youtube = self._mock_youtube()
            youtube.videos().insert().next_chunk.side_effect = ConnectionError("lost response")
            with patch.dict(sys.modules, self._fake_modules(youtube)):
                with patch.object(youtube_upload, "credentials_from_env", return_value=object()):
                    with self.assertRaisesRegex(ConnectionError, "lost response"):
                        youtube_upload.upload(video, {"title": "Test", "description": "Test"},
                                              False, False, False, receipt)
            saved = json.loads(receipt.read_text(encoding="utf-8"))
            self.assertIsNone(saved["video_id"])
            self.assertEqual(saved["upload_state"], "RESULT_UNKNOWN")
            self.assertEqual(saved["source_sha256"], youtube_upload.sha256_file(video))
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
            self.assertEqual(saved["upload_state"], "READBACK_VERIFIED")
            self.assertEqual(saved["actual_privacy_status"], "private")


    def test_existing_unknown_receipt_blocks_retry_without_second_chunk(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "clip.mp4"
            video.write_bytes(b"realistic-test-fixture-not-uploaded")
            receipt = Path(tmp) / "remote.json"
            youtube = self._mock_youtube()
            chunk = youtube.videos().insert().next_chunk
            chunk.side_effect = ConnectionError("ambiguous response")
            with patch.dict(sys.modules, self._fake_modules(youtube)):
                with patch.object(youtube_upload, "credentials_from_env", return_value=object()):
                    with self.assertRaisesRegex(ConnectionError, "ambiguous response"):
                        youtube_upload.upload(video, {"title": "Test", "description": "Test"},
                                              False, False, False, receipt)
                    first = receipt.read_bytes()
                    with self.assertRaisesRegex(RuntimeError, "Existing YouTube upload receipt"):
                        youtube_upload.upload(video, {"title": "Test", "description": "Test"},
                                              False, False, False, receipt)
            self.assertEqual(chunk.call_count, 1)
            self.assertEqual(receipt.read_bytes(), first)
            self.assertEqual(json.loads(first)["upload_state"], "RESULT_UNKNOWN")

    def test_corrupt_existing_receipt_blocks_upload_and_is_not_erased(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "clip.mp4"
            video.write_bytes(b"source")
            receipt = Path(tmp) / "remote.json"
            receipt.write_bytes(b"{partial receipt from interrupted run")
            youtube = self._mock_youtube()
            with patch.dict(sys.modules, self._fake_modules(youtube)):
                with patch.object(youtube_upload, "credentials_from_env", return_value=object()):
                    with self.assertRaisesRegex(RuntimeError, "Existing YouTube upload receipt"):
                        youtube_upload.upload(video, {"title": "Test", "description": "Test"},
                                              False, False, False, receipt)
            youtube.videos().insert().next_chunk.assert_not_called()
            self.assertEqual(receipt.read_bytes(), b"{partial receipt from interrupted run")


    def test_direct_upload_without_receipt_blocks_before_network_or_oauth(self):
        """The library entrypoint cannot bypass the mandatory receipt path."""
        with patch.object(youtube_upload, "credentials_from_env") as credentials:
            with self.assertRaisesRegex(ValueError, "receipt_path is required"):
                youtube_upload.upload(Path("missing.mp4"),
                                      {"title": "Test", "description": "Test"},
                                      False, False, False)
        credentials.assert_not_called()

    def test_cli_fails_closed_without_durable_receipt_path(self):
        """Missing receipt must be rejected before reading media or invoking YouTube."""
        argv = ["youtube_upload.py", "nonexistent.mp4", "meta.json",
                "--preflight", "preflight.json"]
        with patch.object(sys, "argv", argv), patch("sys.stderr", new_callable=io.StringIO) as err:
            with self.assertRaises(SystemExit) as caught:
                youtube_upload.main()
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("--receipt-path", err.getvalue())


if __name__ == "__main__":
    unittest.main()
