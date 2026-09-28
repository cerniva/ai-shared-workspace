from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import shorts_free_pipeline


def packet(*, language: str = "en", voice: str | None = None) -> dict:
    data = {
        "id": "PIPE-001",
        "topic": "A useful engineering fact",
        "why_selected": "Strong hook and practical value",
        "trend_or_evergreen": "evergreen",
        "hook": "This tiny part changes everything.",
        "target_seconds": 18,
        "sources": ["https://example.com/a", "https://example.com/b"],
        "unique_angle": "Show the hidden mechanism",
        "script_beats": ["hook", "mechanism", "payoff"],
        "visual_plan": ["detail", "diagram", "result"],
        "audio_plan": "Narration required",
        "title": "The tiny part that changes everything",
        "hashtags": ["shorts", "engineering"],
        "prepublish_checklist": {
            "facts_verified": True,
            "sources_reliable": True,
            "strong_first_2s": True,
            "no_empty_intro": True,
            "audio_planned": True,
            "portrait_9_16_planned": True,
            "not_previously_published": True,
            "title_matches": True,
            "rights_ok": True,
            "publishable_quality_planned": True,
        },
        "render_requested": False,
        "free_render_requested": True,
        "language": language,
        "content_type": "explainer",
        "narration_text": "First sentence. Second sentence explains the mechanism clearly.",
        "media_queries": ["machine detail", "engineering diagram", "machine detail"],
    }
    if voice is not None:
        data["narration_voice"] = voice
    return data


class ShortsFreePipelineTests(unittest.TestCase):
    """Pin packet-to-render orchestration without network, credits, or publishing."""

    def test_pipeline_refuses_packet_that_fails_research_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            packet_path = root / "packet.json"
            packet_path.write_text(json.dumps({"free_render_requested": True}), encoding="utf-8")
            with patch("scripts.shorts_free_pipeline.search_free_media") as search:
                with self.assertRaises(ValueError):
                    shorts_free_pipeline.prepare_render_bundle(packet_path, root / "work", env={})
                search.assert_not_called()

    @patch("scripts.shorts_free_pipeline.download_asset")
    @patch("scripts.shorts_free_pipeline.search_free_media")
    def test_pipeline_uses_media_queries_in_order_and_deduplicates_assets(self, search, download) -> None:
        search.side_effect = [
            [{"provider": "pexels", "provider_asset_id": "1", "source_url": "https://src/1", "download_url": "https://cdn/1.mp4", "media_type": "video", "license_note": "ok", "creator": None, "retrieved_at": "2026-09-28T00:00:00Z"}],
            [{"provider": "pixabay", "provider_asset_id": "2", "source_url": "https://src/2", "download_url": "https://cdn/2.mp4", "media_type": "video", "license_note": "ok", "creator": None, "retrieved_at": "2026-09-28T00:00:00Z"}],
        ]
        download.side_effect = lambda asset, destination: destination.write_bytes(b"x") or destination
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            packet_path = root / "packet.json"
            packet_path.write_text(json.dumps(packet()), encoding="utf-8")
            bundle = shorts_free_pipeline.prepare_render_bundle(packet_path, root / "work", env={})
            self.assertEqual([call.args[0] for call in search.call_args_list], ["machine detail", "engineering diagram"])
            self.assertEqual(len(bundle["assets"]), 2)

    @patch("scripts.shorts_free_pipeline.download_asset")
    @patch("scripts.shorts_free_pipeline.search_free_media")
    def test_pipeline_writes_provenance_without_secrets(self, search, download) -> None:
        search.return_value = [{"provider": "pexels", "provider_asset_id": "1", "source_url": "https://src/1", "download_url": "https://cdn/1.mp4", "media_type": "video", "license_note": "ok", "creator": None, "retrieved_at": "2026-09-28T00:00:00Z"}]
        download.side_effect = lambda asset, destination: destination.write_bytes(b"x") or destination
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            packet_path = root / "packet.json"
            packet_path.write_text(json.dumps(packet()), encoding="utf-8")
            bundle = shorts_free_pipeline.prepare_render_bundle(packet_path, root / "work", env={"PEXELS_API_KEY": "TOPSECRET"})
            text = Path(bundle["provenance"]).read_text(encoding="utf-8")
            self.assertNotIn("TOPSECRET", text)
            self.assertIn('"provider": "pexels"', text)

    def test_turkish_packet_defaults_to_tr_voice(self) -> None:
        self.assertEqual(shorts_free_pipeline.default_espeak_voice("tr-TR"), "tr")

    def test_english_packet_defaults_to_en_us_voice(self) -> None:
        self.assertEqual(shorts_free_pipeline.default_espeak_voice("en-GB"), "en-us")

    def test_unknown_language_requires_explicit_narration_voice(self) -> None:
        with self.assertRaises(ValueError):
            shorts_free_pipeline.default_espeak_voice("de-DE")
        self.assertEqual(shorts_free_pipeline.default_espeak_voice("de-DE", "de"), "de")

    def test_build_srt_uses_mobile_readable_chunks_and_packet_language_text(self) -> None:
        text = "Bu cümle mobil ekranda okunabilir parçalara ayrılmalı ve anlamını korumalı."
        srt = shorts_free_pipeline.build_srt(text, 12, max_chars=30)
        self.assertIn("00:00:00,000 -->", srt)
        self.assertIn("Bu cümle", srt)
        for line in srt.splitlines():
            if line and "-->" not in line and not line.isdigit():
                self.assertLessEqual(len(line), 30)

    @patch("scripts.shorts_free_pipeline.download_asset")
    @patch("scripts.shorts_free_pipeline.search_free_media")
    def test_render_manifest_contains_local_paths_only(self, search, download) -> None:
        search.return_value = [{"provider": "openverse", "provider_asset_id": "img1", "source_url": "https://src/img1", "download_url": "https://cdn/img1.jpg", "media_type": "image", "license_note": "cc", "creator": None, "retrieved_at": "2026-09-28T00:00:00Z"}]
        download.side_effect = lambda asset, destination: destination.write_bytes(b"x") or destination
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            packet_path = root / "packet.json"
            packet_path.write_text(json.dumps(packet(language="tr")), encoding="utf-8")
            bundle = shorts_free_pipeline.prepare_render_bundle(packet_path, root / "work", env={})
            manifest = json.loads(Path(bundle["render_manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["narration_voice"], "tr")
            self.assertTrue(all(not item["path"].startswith("http") for item in manifest["visuals"]))
            self.assertFalse(str(manifest["subtitles"]).startswith("http"))


if __name__ == "__main__":
    unittest.main()
