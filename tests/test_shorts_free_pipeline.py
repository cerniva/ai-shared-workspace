import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import call, patch

try:
    from scripts import shorts_free_pipeline as pipeline
except ImportError:
    pipeline = None

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "shorts_free_pipeline.py"

CRITICAL_CHECKS = {
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
}


def valid_packet(language="en", narration="A short original narration for the pipeline."):
    return {
        "topic": "Pipeline fixture topic zx7314",
        "why_selected": "test fixture",
        "trend_or_evergreen": "evergreen",
        "hook": "ZX7314 pipeline hook",
        "target_seconds": 18,
        "sources": ["https://example.com/a", "https://example.com/b"],
        "unique_angle": "pipeline fixture angle",
        "script_beats": ["one", "two"],
        "visual_plan": ["stock visual"],
        "audio_plan": "narration",
        "title": "ZX7314 pipeline title",
        "hashtags": ["#test"],
        "prepublish_checklist": dict(CRITICAL_CHECKS),
        "free_render_requested": True,
        "language": language,
        "content_type": "short_fact",
        "narration_text": narration,
        "media_queries": ["vertical forest", "vertical river"],
    }


def asset(provider, asset_id, media_type="video", suffix="mp4"):
    return {
        "provider": provider,
        "provider_asset_id": asset_id,
        "source_url": f"https://example.com/source/{asset_id}",
        "download_url": f"https://example.com/media/{asset_id}.{suffix}",
        "media_type": media_type,
        "license_note": "test license",
        "creator": "fixture creator",
        "retrieved_at": "2026-09-28T00:00:00Z",
    }


def fake_download(item, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(b"fixture")
    return destination


class ShortsFreePipelineTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(pipeline, "scripts.shorts_free_pipeline must exist")

    def _write_packet(self, base: Path, packet: dict) -> Path:
        path = base / "packet.json"
        path.write_text(json.dumps(packet, ensure_ascii=False), encoding="utf-8")
        return path

    def test_pipeline_refuses_packet_that_fails_research_gate(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            packet = valid_packet()
            packet["prepublish_checklist"]["rights_ok"] = False
            packet_path = self._write_packet(base, packet)
            with patch.object(pipeline, "search_free_media") as search:
                with self.assertRaisesRegex(ValueError, "research gate"):
                    pipeline.prepare_render_bundle(packet_path, base / "work", env={})
            search.assert_not_called()

    def test_pipeline_uses_media_queries_in_order_and_deduplicates_assets(self):
        first = [asset("pexels", "same"), asset("pexels", "unique-a")]
        second = [asset("pexels", "same"), asset("pixabay", "unique-b")]
        with tempfile.TemporaryDirectory() as td, \
             patch.object(pipeline, "search_free_media", side_effect=[first, second]) as search, \
             patch.object(pipeline, "download_asset", side_effect=fake_download):
            base = Path(td)
            result = pipeline.prepare_render_bundle(
                self._write_packet(base, valid_packet()), base / "work", env={}
            )
            search.assert_has_calls([
                call("vertical forest", env={}, limit=6),
                call("vertical river", env={}, limit=6),
            ])
            self.assertEqual(len(result["assets"]), 3)
            provenance = json.loads(Path(result["provenance"]).read_text(encoding="utf-8"))
            self.assertEqual(
                [(item["provider"], item["provider_asset_id"]) for item in provenance],
                [("pexels", "same"), ("pexels", "unique-a"), ("pixabay", "unique-b")],
            )

    def test_pipeline_writes_provenance_without_secrets(self):
        secret_env = {
            "PEXELS_API_KEY": "pexels-secret-value-123",
            "PIXABAY_API_KEY": "pixabay-secret-value-456",
        }
        with tempfile.TemporaryDirectory() as td, \
             patch.object(pipeline, "search_free_media", return_value=[asset("pexels", "1")]), \
             patch.object(pipeline, "download_asset", side_effect=fake_download):
            base = Path(td)
            result = pipeline.prepare_render_bundle(
                self._write_packet(base, valid_packet()), base / "work", env=secret_env
            )
            text = Path(result["provenance"]).read_text(encoding="utf-8")
            self.assertNotIn(secret_env["PEXELS_API_KEY"], text)
            self.assertNotIn(secret_env["PIXABAY_API_KEY"], text)
            self.assertIn('"provider": "pexels"', text)

    def test_turkish_packet_defaults_to_tr_voice(self):
        self.assertEqual(pipeline.default_espeak_voice("tr"), "tr")
        self.assertEqual(pipeline.default_espeak_voice("tr-TR"), "tr")

    def test_english_packet_defaults_to_en_us_voice(self):
        self.assertEqual(pipeline.default_espeak_voice("en"), "en-us")
        self.assertEqual(pipeline.default_espeak_voice("en-GB"), "en-us")

    def test_unknown_language_requires_explicit_narration_voice(self):
        with self.assertRaisesRegex(ValueError, "narration_voice"):
            pipeline.default_espeak_voice("de")
        self.assertEqual(pipeline.default_espeak_voice("de", "de"), "de")

    def test_build_srt_uses_mobile_readable_chunks_and_packet_language_text(self):
        text = "Türkiye için kısa altyazı metni mobil ekranda rahat okunmalı ve anlam korunmalı."
        srt = pipeline.build_srt(text, 12, max_chars=24)
        caption_lines = [
            line for line in srt.splitlines()
            if line and " --> " not in line and not line.isdigit()
        ]
        self.assertGreater(len(caption_lines), 1)
        self.assertTrue(all(len(line) <= 24 for line in caption_lines))
        self.assertEqual(" ".join(caption_lines), text)

    def test_render_manifest_contains_local_paths_only(self):
        with tempfile.TemporaryDirectory() as td, \
             patch.object(pipeline, "search_free_media", return_value=[asset("pixabay", "2")]), \
             patch.object(pipeline, "download_asset", side_effect=fake_download):
            base = Path(td)
            result = pipeline.prepare_render_bundle(
                self._write_packet(base, valid_packet()), base / "work", env={}
            )
            manifest = json.loads(Path(result["render_manifest"]).read_text(encoding="utf-8"))
            self.assertEqual(manifest["narration_voice"], "en-us")
            self.assertEqual(manifest["subtitles"], "captions.srt")
            self.assertTrue(manifest["visuals"])
            for visual in manifest["visuals"]:
                self.assertFalse(visual["path"].startswith(("http://", "https://", "/")))
                self.assertTrue(visual["path"].startswith("assets/"))

    def test_direct_cli_help_runs_without_repo_import_error(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertNotIn("ModuleNotFoundError", result.stderr)


if __name__ == "__main__":
    unittest.main()
