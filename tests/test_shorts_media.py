from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import shorts_media


class ShortsMediaTests(unittest.TestCase):
    """Define normalization, fallback, redaction, and download safety."""

    @patch("scripts.shorts_media.urlopen")
    def test_request_json_sends_explicit_app_headers_and_preserves_auth(self, urlopen) -> None:
        """Provider API calls should identify the app and still keep provider auth headers."""
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b"{}"

        urlopen.return_value = FakeResponse()

        result = shorts_media._request_json(
            "https://api.example.test/search",
            headers={"Authorization": "provider-key"},
        )

        self.assertEqual(result, {})
        request = urlopen.call_args.args[0]
        headers = {key.casefold(): value for key, value in request.header_items()}
        self.assertEqual(
            headers["user-agent"],
            "cerniva-shorts-media/1.0 (+https://github.com/cerniva/ai-shared-workspace)",
        )
        self.assertEqual(headers["accept"], "application/json")
        self.assertEqual(headers["authorization"], "provider-key")

    @patch("scripts.shorts_media._request_json")
    def test_pexels_video_response_normalizes_to_media_asset(self, request_json) -> None:
        """Pexels video search should emit the shared media-asset schema."""
        request_json.return_value = {
            "videos": [
                {
                    "id": 123,
                    "url": "https://www.pexels.com/video/example-123/",
                    "user": {"name": "Pexels Creator"},
                    "video_files": [
                        {"link": "https://cdn.example/small.mp4", "width": 640, "height": 360},
                        {"link": "https://cdn.example/large.mp4", "width": 1920, "height": 1080},
                    ],
                }
            ]
        }
        assets = shorts_media.search_pexels("city", "pexels-secret", limit=4)
        self.assertEqual(len(assets), 1)
        asset = assets[0]
        self.assertEqual(asset["provider"], "pexels")
        self.assertEqual(asset["provider_asset_id"], "123")
        self.assertEqual(asset["source_url"], "https://www.pexels.com/video/example-123/")
        self.assertEqual(asset["download_url"], "https://cdn.example/large.mp4")
        self.assertEqual(asset["media_type"], "video")
        self.assertEqual(asset["creator"], "Pexels Creator")
        self.assertTrue(asset["license_note"])
        self.assertTrue(asset["retrieved_at"].endswith("Z"))
        called_url = request_json.call_args.args[0]
        called_headers = request_json.call_args.kwargs["headers"]
        self.assertIn("/v1/videos/search", called_url)
        self.assertEqual(called_headers["Authorization"], "pexels-secret")

    @patch("scripts.shorts_media._request_json")
    def test_pixabay_video_response_normalizes_to_media_asset(self, request_json) -> None:
        """Pixabay video search should normalize its best available video file."""
        request_json.return_value = {
            "hits": [
                {
                    "id": 456,
                    "pageURL": "https://pixabay.com/videos/id-456/",
                    "user": "Pixabay Creator",
                    "videos": {
                        "small": {"url": "https://cdn.example/small.mp4", "width": 640, "height": 360},
                        "large": {"url": "https://cdn.example/large.mp4", "width": 1920, "height": 1080},
                    },
                }
            ]
        }
        assets = shorts_media.search_pixabay("ocean", "pixabay-secret", limit=5)
        self.assertEqual(len(assets), 1)
        asset = assets[0]
        self.assertEqual(asset["provider"], "pixabay")
        self.assertEqual(asset["provider_asset_id"], "456")
        self.assertEqual(asset["download_url"], "https://cdn.example/large.mp4")
        self.assertEqual(asset["media_type"], "video")
        self.assertEqual(asset["creator"], "Pixabay Creator")
        called_url = request_json.call_args.args[0]
        self.assertIn("https://pixabay.com/api/videos/", called_url)
        self.assertIn("key=pixabay-secret", called_url)

    @patch("scripts.shorts_media._request_json")
    def test_openverse_result_requires_explicit_license_and_normalizes(self, request_json) -> None:
        """Openverse should keep only image results with explicit license provenance."""
        request_json.return_value = {
            "results": [
                {
                    "id": "licensed",
                    "url": "https://images.example/licensed.jpg",
                    "foreign_landing_url": "https://source.example/licensed",
                    "license": "by",
                    "license_url": "https://creativecommons.org/licenses/by/4.0/",
                    "creator": "Open Creator",
                },
                {
                    "id": "missing-license",
                    "url": "https://images.example/missing.jpg",
                    "foreign_landing_url": "https://source.example/missing",
                    "license": "",
                    "license_url": "",
                    "creator": "Unknown",
                },
            ]
        }
        assets = shorts_media.search_openverse("mountain", limit=3)
        self.assertEqual([item["provider_asset_id"] for item in assets], ["licensed"])
        self.assertEqual(assets[0]["provider"], "openverse")
        self.assertEqual(assets[0]["media_type"], "image")
        self.assertIn("creativecommons.org", assets[0]["license_note"])

    @patch("scripts.shorts_media.search_pixabay")
    @patch("scripts.shorts_media.search_pexels")
    def test_missing_pexels_key_falls_back_to_pixabay(self, search_pexels, search_pixabay) -> None:
        """A missing Pexels secret should not block a configured Pixabay provider."""
        search_pixabay.return_value = [{"provider": "pixabay"}]
        assets = shorts_media.search_free_media(
            "robot",
            env={"PIXABAY_API_KEY": "pix-key"},
        )
        search_pexels.assert_not_called()
        search_pixabay.assert_called_once_with("robot", "pix-key", limit=12)
        self.assertEqual(assets, [{"provider": "pixabay"}])

    @patch("scripts.shorts_media.search_openverse")
    @patch("scripts.shorts_media.search_pixabay")
    @patch("scripts.shorts_media.search_pexels")
    def test_missing_both_keys_falls_back_to_openverse(
        self,
        search_pexels,
        search_pixabay,
        search_openverse,
    ) -> None:
        """Openverse images should remain a no-secret fallback when both video keys are absent."""
        search_openverse.return_value = [{"provider": "openverse"}]
        assets = shorts_media.search_free_media("forest", env={})
        search_pexels.assert_not_called()
        search_pixabay.assert_not_called()
        search_openverse.assert_called_once_with("forest", limit=12)
        self.assertEqual(assets, [{"provider": "openverse"}])

    @patch("scripts.shorts_media._request_json")
    def test_empty_or_malformed_provider_payload_does_not_create_asset(self, request_json) -> None:
        """Malformed or empty upstream payloads must never become bogus media records."""
        request_json.return_value = {"videos": "not-a-list"}
        self.assertEqual(shorts_media.search_pexels("bad", "key"), [])
        request_json.return_value = {"hits": [{}]}
        self.assertEqual(shorts_media.search_pixabay("bad", "key"), [])

    @patch("scripts.shorts_media._request_json")
    def test_pixabay_key_is_redacted_from_error_text(self, request_json) -> None:
        """Provider failures must not expose a Pixabay key embedded in an authenticated URL."""
        request_json.side_effect = RuntimeError(
            "request failed: https://pixabay.com/api/videos/?key=super-secret-key&q=city"
        )
        with self.assertRaises(shorts_media.MediaProviderError) as raised:
            shorts_media.search_pixabay("city", "super-secret-key")
        message = str(raised.exception)
        self.assertNotIn("super-secret-key", message)
        self.assertIn("[REDACTED]", message)

    def test_download_asset_rejects_non_http_url(self) -> None:
        """Asset download must reject file/data schemes before any filesystem write."""
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "asset.mp4"
            with self.assertRaises(ValueError):
                shorts_media.download_asset(
                    {"download_url": "file:///etc/passwd"},
                    target,
                )
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
