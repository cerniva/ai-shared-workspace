"""Regression tests for atomic sourced-Short promotion; synthetic bytes only."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.shorts_source_clip import file_sha256, render


class AtomicShortsGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "source.mp4"
        self.source.write_bytes(b"synthetic fixture - not licensed media")
        self.srt = self.root / "captions.srt"
        self.srt.write_text(
            "1\n00:00:00,000 --> 00:00:30,000\nTest speech\n", encoding="utf-8"
        )
        self.rights = self.root / "rights.json"
        self.rights.write_text(json.dumps({
            "source_url": "https://example.org/fixture",
            "license_url": "https://example.org/fixture-rights",
            "license_name": "TEST FIXTURE ONLY",
            "verified_by": "unit test",
            "verified_at": "2026-10-23",
            "source_sha256": file_sha256(self.source),
            "captions_sha256": file_sha256(self.srt),
            "caption_source_url": "https://example.org/fixture-caption",
            "caption_license_url": "https://example.org/fixture-caption-license",
            "caption_license_name": "TEST FIXTURE ONLY",
            "caption_verified_by": "unit test",
            "caption_verified_at": "2026-10-23",
            "caption_reuse_permitted": True,
            "caption_derivatives_permitted": True,
            "reuse_permitted": True,
            "derivatives_permitted": True,
            "audio_reuse_permitted": True,
            "spoken_language": "en",
            "caption_language": "en",
        }), encoding="utf-8")
        self.output = self.root / "final.mp4"

    @staticmethod
    def fake_probe(path):
        if Path(path).name == "source.mp4":
            return {"format": {"duration": "35"}, "streams": [
                {"codec_type": "video", "width": 640, "height": 360},
                {"codec_type": "audio"},
            ]}
        return {"format": {"duration": "30"}, "streams": [
            {"codec_type": "video", "width": 1080, "height": 1920, "duration": "30"},
            {"codec_type": "audio", "duration": "30"},
        ]}

    @staticmethod
    def fake_ffmpeg(command, **kwargs):
        # FFmpeg is mocked here. Actual FFmpeg smoke/QC is a separate gate.
        Path(command[-1]).write_bytes(b"synthetic MP4 fixture")
        return SimpleNamespace(returncode=0, stderr="")

    def run_render(self, motion_status):
        with patch("scripts.shorts_source_clip._probe", side_effect=self.fake_probe), \
             patch("scripts.shorts_source_clip.shutil.which", return_value="/usr/bin/ffmpeg"), \
             patch("scripts.shorts_source_clip.subprocess.run", side_effect=self.fake_ffmpeg), \
             patch("scripts.shorts_motion_qc.inspect", return_value={"motion_qc": motion_status}), \
             patch("scripts.shorts_audio_qc.inspect", return_value={"audio_qc": "PASS_TECHNICAL_ONLY"}):
            return render(self.source, self.srt, self.rights, self.output,
                          start=0, seconds=30, language="en")

    def test_motion_rejection_leaves_no_final_mp4(self):
        with self.assertRaisesRegex(RuntimeError, "motion QC_BLOCKED"):
            self.run_render("QC_BLOCKED")
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob("licensed-short-*")), [])

    def test_technical_pass_promotes_one_mp4_but_not_publish_ready(self):
        report = self.run_render("PASS_TECHNICAL_ONLY")
        self.assertTrue(self.output.is_file())
        self.assertEqual(report["output_sha256"], file_sha256(self.output))
        self.assertFalse(report["publish_ready"])
        self.assertTrue(report["independent_media_review_pending"])
        self.assertEqual(list(self.root.glob("licensed-short-*")), [])

    def test_audio_rejection_leaves_no_final_mp4(self):
        with patch("scripts.shorts_source_clip._probe", side_effect=self.fake_probe), \
             patch("scripts.shorts_source_clip.shutil.which", return_value="/usr/bin/ffmpeg"), \
             patch("scripts.shorts_source_clip.subprocess.run", side_effect=self.fake_ffmpeg), \
             patch("scripts.shorts_motion_qc.inspect", return_value={"motion_qc": "PASS_TECHNICAL_ONLY"}), \
             patch("scripts.shorts_audio_qc.inspect", return_value={"audio_qc": "QC_BLOCKED"}):
            with self.assertRaisesRegex(RuntimeError, "audio QC_BLOCKED"):
                render(self.source, self.srt, self.rights, self.output,
                       start=0, seconds=30, language="en")
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob("licensed-short-*")), [])

    def test_race_output_created_during_ffmpeg_is_not_overwritten(self):
        # Simulate a second process creating the destination after the
        # initial exists() check, but before candidate promotion.
        def racing_ffmpeg(command, **kwargs):
            self.output.write_bytes(b"concurrent final")
            return self.fake_ffmpeg(command, **kwargs)

        with patch("scripts.shorts_source_clip._probe", side_effect=self.fake_probe), \
             patch("scripts.shorts_source_clip.shutil.which", return_value="/usr/bin/ffmpeg"), \
             patch("scripts.shorts_source_clip.subprocess.run", side_effect=racing_ffmpeg), \
             patch("scripts.shorts_motion_qc.inspect", return_value={"motion_qc": "PASS_TECHNICAL_ONLY"}), \
             patch("scripts.shorts_audio_qc.inspect", return_value={"audio_qc": "PASS_TECHNICAL_ONLY"}):
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                render(self.source, self.srt, self.rights, self.output,
                       start=0, seconds=30, language="en")
        self.assertEqual(self.output.read_bytes(), b"concurrent final")
        self.assertEqual(list(self.root.glob("licensed-short-*")), [])

    def test_existing_output_is_not_overwritten(self):
        self.output.write_bytes(b"previous file")
        with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
            self.run_render("PASS_TECHNICAL_ONLY")
        self.assertEqual(self.output.read_bytes(), b"previous file")


if __name__ == "__main__":
    unittest.main()
