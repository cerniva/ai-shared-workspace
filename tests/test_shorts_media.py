import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from scripts import shorts_media as media
except ImportError:
    media = None


class ShortsMediaTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(media, "scripts.shorts_media must exist")

    def test_pexels_video_response_normalizes_to_media_asset(self):
        payload = {
            "videos": [{
                "id": 123,
                "url": "https://www.pexels.com/video/sample-123/",
                "user": {"name": "Creator"},
                "video_files": [{
                    "id": 1,
                    "quality": "hd",
                    "width": 1080,
                    "height": 1920,
                    "link": "https://videos.pexels.com/video-files/sample.mp4",
                }],
            }]
        }
        with patch.object(media, "_request_json", return_value=payload) as request_json:
            results = media.search_pexels("vertical city", "pexels-secret", limit=4)

        self.assertEqual(len(results), 1)
        asset = results[0]
        self.assertEqual(asset["provider"], "pexels")
        self.assertEqual(asset["provider_asset_id"], "123")
        self.assertEqual(asset["media_type"], "video")
        self.assertEqual(asset["source_url"], "https://www.pexels.com/video/sample-123/")
        self.assertEqual(asset["download_url"], "https://videos.pexels.com/video-files/sample.mp4")
        self.assertEqual(asset["creator"], "Creator")
        self.assertIn("Pexels", asset["license_note"])
        self.assertTrue(asset["retrieved_at"].endswith("Z"))
        headers = request_json.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "pexels-secret")
        self.assertNotIn("pexels-secret", request_json.call_args.args[0])

    def test_pixabay_video_response_normalizes_to_media_asset(self):
        payload = {
            "hits": [{
                "id": 456,
                "pageURL": "https://pixabay.com/videos/id-456/",
                "user": "PixCreator",
                "videos": {
                    "large": {"url": "https://cdn.pixabay.com/video/large.mp4", "width": 1920, "height": 1080},
                    "medium": {"url": "https://cdn.pixabay.com/video/medium.mp4", "width": 1280, "height": 720},
                },
            }]
        }
        with patch.object(media, "_request_json", return_value=payload):
            results = media.search_pixabay("ocean", "pix-secret", limit=3)

        self.assertEqual(len(results), 1)
        asset = results[0]
        self.assertEqual(asset["provider"], "pixabay")
        self.assertEqual(asset["provider_asset_id"], "456")
        self.assertEqual(asset["media_type"], "video")
        self.assertEqual(asset["download_url"], "https://cdn.pixabay.com/video/large.mp4")
        self.assertEqual(asset["creator"], "PixCreator")
        self.assertIn("Pixabay", asset["license_note"])

    def test_openverse_result_requires_explicit_license_and_normalizes(self):
        payload = {
            "results": [
                {
                    "id": "ok",
                    "foreign_landing_url": "https://example.org/item/ok",
                    "url": "https://example.org/media/ok.jpg",
                    "creator": "Open Creator",
                    "license": "cc0",
                    "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
                },
                {
                    "id": "missing-license",
                    "foreign_landing_url": "https://example.org/item/bad",
                    "url": "https://example.org/media/bad.jpg",
                    "creator": "Unknown",
                    "license": "",
                    "license_url": "",
                },
            ]
        }
        with patch.object(media, "_request_json", return_value=payload):
            results = media.search_openverse("space", limit=5)

        self.assertEqual([item["provider_asset_id"] for item in results], ["ok"])
        self.assertEqual(results[0]["provider"], "openverse")
        self.assertEqual(results[0]["media_type"], "image")
        self.assertIn("cc0", results[0]["license_note"].lower())
        self.assertIn("creativecommons.org", results[0]["license_note"])

    def test_missing_pexels_key_falls_back_to_pixabay(self):
        expected = [{"provider": "pixabay", "provider_asset_id": "1"}]
        with patch.object(media, "search_pexels") as pexels, \
             patch.object(media, "search_pixabay", return_value=expected) as pixabay, \
             patch.object(media, "search_openverse") as openverse:
            result = media.search_free_media("forest", env={"PIXABAY_API_KEY": "pix-key"}, limit=2)
        pexels.assert_not_called()
        pixabay.assert_called_once_with("forest", "pix-key", limit=2)
        openverse.assert_not_called()
        self.assertEqual(result, expected)

    def test_missing_both_keys_falls_back_to_openverse(self):
        expected = [{"provider": "openverse", "provider_asset_id": "ov"}]
        with patch.object(media, "search_pexels") as pexels, \
             patch.object(media, "search_pixabay") as pixabay, \
             patch.object(media, "search_openverse", return_value=expected) as openverse:
            result = media.search_free_media("forest", env={}, limit=2)
        pexels.assert_not_called()
        pixabay.assert_not_called()
        openverse.assert_called_once_with("forest", limit=2)
        self.assertEqual(result, expected)

    def test_empty_or_malformed_provider_payload_does_not_create_asset(self):
        bad_payloads = [{}, {"videos": None}, {"videos": [{"id": 1}]}, {"videos": "not-a-list"}]
        for payload in bad_payloads:
            with self.subTest(payload=payload), patch.object(media, "_request_json", return_value=payload):
                self.assertEqual(media.search_pexels("bad", "key"), [])

    def test_pixabay_key_is_redacted_from_error_text(self):
        secret = "pixabay-super-secret-key-12345"
        leaked = f"request failed: https://pixabay.com/api/videos/?key={secret}&q=city"
        with patch.object(media, "_request_json", side_effect=RuntimeError(leaked)):
            with self.assertRaises(RuntimeError) as caught:
                media.search_pixabay("city", secret)
        text = str(caught.exception)
        self.assertNotIn(secret, text)
        self.assertIn("[REDACTED]", text)

    def test_download_asset_rejects_non_http_url(self):
        asset = {"download_url": "file:///etc/passwd"}
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, "http"):
                media.download_asset(asset, Path(td) / "asset.bin")


if __name__ == "__main__":
    unittest.main()
