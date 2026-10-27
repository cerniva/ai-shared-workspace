"""Fail-closed tests for preserving sourced footage/audio; no network or YouTube."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.shorts_source_clip import check_captions, file_sha256, render, validate_rights


class SourceClipTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.video = self.root / "source.mp4"
        self.video.write_bytes(b"synthetic source fixture")
        self.srt = self.root / "captions.srt"
        self.srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello world\n\n"
                            "2\n00:00:04,000 --> 00:00:10,000\nAnother sentence\n")
        self.evidence = self.root / "rights.json"
        self.data = {
            "source_url": "https://example.org/owned-source",
            "license_url": "https://example.org/permission",
            "license_name": "Written permission",
            "source_sha256": file_sha256(self.video),
            "caption_sha256": file_sha256(self.srt),
            "caption_license_name": "TEST fixture captions",
            "caption_license_url": "https://example.org/caption-license",
            "caption_reuse_permitted": True,
            "caption_derivatives_permitted": True,
            "reuse_permitted": True,
            "derivatives_permitted": True,
            "audio_reuse_permitted": True,
            "verified_at": "2026-10-20",
            "verified_by": "Test fixture only",
            "spoken_language": "en",
            "caption_language": "en",
        }
        self.evidence.write_text(json.dumps(self.data))

    def refresh_caption_hash(self):
        self.data["caption_sha256"] = file_sha256(self.srt)
        self.evidence.write_text(json.dumps(self.data))

    def test_source_mutation_after_rights_check_blocks_render(self):
        # Simulate a source file being swapped after the original SHA was approved.
        # FFmpeg must never open the replacement bytes or publish an output.
        self.srt.write_text("1\n00:00:00,000 --> 00:00:30,000\nHello world\n")
        self.refresh_caption_hash()
        original_validate = validate_rights

        def swap_after_validation(*args):
            evidence = original_validate(*args)
            self.video.write_bytes(b"unlicensed replacement after hash check")
            return evidence

        output = self.root / "should-not-exist.mp4"
        with patch("scripts.shorts_source_clip.validate_rights", side_effect=swap_after_validation), \
             patch("scripts.shorts_source_clip.shutil.which", return_value="/usr/bin/ffmpeg"):
            with self.assertRaisesRegex(ValueError, "source changed during rights-checked snapshot"):
                render(self.video, self.srt, self.evidence, output,
                       start=0, seconds=30, language="en")
        self.assertFalse(output.exists())

    def test_caption_swap_during_snapshot_blocks_render(self):
        # An attacker can replace the SRT between initial validation and copy.
        # The renderer must validate the exact private SRT that FFmpeg reads.
        import shutil
        self.srt.write_text("1\n00:00:00,000 --> 00:00:30,000\nOriginal valid caption\n")
        self.refresh_caption_hash()
        original_copy = shutil.copyfile

        def swap_on_caption_copy(src, dst, *args, **kwargs):
            if Path(src) == self.srt:
                self.srt.write_text("1\n00:00:00,000 --> 00:00:20,000\nTampered\n\n"
                                    "2\n00:00:19,000 --> 00:00:30,000\nOverlapping\n")
            return original_copy(src, dst, *args, **kwargs)

        output = self.root / "caption-swap-must-block.mp4"
        with patch("scripts.shorts_source_clip.shutil.copyfile", side_effect=swap_on_caption_copy), \
             patch("scripts.shorts_source_clip.shutil.which", return_value="/usr/bin/ffmpeg"):
            with self.assertRaisesRegex(ValueError, "captions changed during rights-checked snapshot"):
                render(self.video, self.srt, self.evidence, output,
                       start=0, seconds=30, language="en")
        self.assertFalse(output.exists())

    def test_valid_rights_record(self):
        self.assertEqual(validate_rights(self.video, self.srt, self.evidence, "en")["spoken_language"], "en")

    def test_missing_audio_rights_blocks(self):
        self.data["audio_reuse_permitted"] = False
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "audio_reuse_permitted"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_hash_mismatch_blocks(self):
        self.data["source_sha256"] = "0" * 64
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "hash"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_caption_hash_mismatch_blocks(self):
        self.data["caption_sha256"] = "0" * 64
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "caption hash"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_missing_caption_license_blocks(self):
        del self.data["caption_license_url"]
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "caption_license_url"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_caption_derivative_permission_blocks(self):
        self.data["caption_derivatives_permitted"] = False
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "caption_derivatives_permitted"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_caption_reuse_permission_blocks(self):
        self.data["caption_reuse_permitted"] = False
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "caption_reuse_permitted"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_language_mismatch_blocks(self):
        with self.assertRaisesRegex(ValueError, "spoken_language"):
            validate_rights(self.video, self.srt, self.evidence, "tr")

    def test_srt_outside_clip_blocks(self):
        self.srt.write_text("1\n00:00:00,000 --> 00:00:31,000\nHello\n")
        with self.assertRaisesRegex(ValueError, "beyond clip"):
            check_captions(self.srt, 30)

    def test_srt_overlap_blocks(self):
        self.srt.write_text("1\n00:00:00,000 --> 00:00:05,000\nHello\n\n"
                            "2\n00:00:04,000 --> 00:00:06,000\nWorld\n")
        with self.assertRaisesRegex(ValueError, "overlap"):
            check_captions(self.srt, 30)

    def test_overfast_srt_blocks_before_render(self):
        # A timed transcript is not necessarily readable on a phone.
        self.srt.write_text("1\n00:00:00,000 --> 00:00:01,000\n"
                            "This sentence is far too long to read in one second\n\n"
                            "2\n00:00:01,000 --> 00:00:30,000\nEnd\n")
        with self.assertRaisesRegex(ValueError, "reading speed exceeds 20"):
            check_captions(self.srt, 30)

    def test_readable_srt_passes_speed_gate(self):
        self.srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nHello world\n\n"
                            "2\n00:00:02,000 --> 00:00:30,000\nReadable\n")
        self.assertIsNone(check_captions(self.srt, 30))

    def test_landscape_caption_margin_uses_ass_units_inside_image(self):
        from scripts.shorts_source_clip import _caption_margin_ass_units
        # A 16:9 source is 608px high when padded to 1080x1920.
        # ASS PlayResY=288: 112 script units = about 747 output pixels.
        self.assertEqual(_caption_margin_ass_units(1920, 1080), 112)
        self.assertLess(_caption_margin_ass_units(1920, 1080), 288)

    def test_portrait_caption_margin_stays_in_bottom_safe_area(self):
        from scripts.shorts_source_clip import _caption_margin_ass_units
        self.assertEqual(_caption_margin_ass_units(1080, 1920), 18)

    def test_caption_margin_rejects_invalid_source_dimensions(self):
        from scripts.shorts_source_clip import _caption_margin_ass_units
        with self.assertRaisesRegex(ValueError, "dimensions"):
            _caption_margin_ass_units(0, 1080)

    def test_short_duration_blocks_before_ffmpeg(self):
        with self.assertRaisesRegex(ValueError, "30–40"):
            render(self.video, self.srt, self.evidence, self.root / "out.mp4",
                   start=0, seconds=29, language="en")

    def test_empty_subtitles_block(self):
        self.srt.write_text("")
        with self.assertRaisesRegex(ValueError, "timed SRT"):
            check_captions(self.srt, 30)

    def test_non_https_rights_block(self):
        self.data["source_url"] = "http://example.org/video"
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            validate_rights(self.video, self.srt, self.evidence, "en")



    def test_srt_timestamp_without_spoken_text_blocks(self):
        self.srt.write_text("1\n00:00:00,000 --> 00:00:03,000\n  \n")
        with self.assertRaisesRegex(ValueError, "caption cue text missing"):
            check_captions(self.srt, 32)

    def test_srt_markup_only_blocks(self):
        self.srt.write_text("1\n00:00:00,000 --> 00:00:03,000\n<i></i>\n")
        with self.assertRaisesRegex(ValueError, "caption cue text missing"):
            check_captions(self.srt, 32)

    def test_rendered_audio_coverage_blocks_short_track(self):
        from scripts.shorts_source_clip import _require_audio_coverage
        with self.assertRaisesRegex(RuntimeError, "does not cover full clip"):
            _require_audio_coverage([{"codec_type": "audio", "duration": "25.0"}], 32)

    def test_rendered_audio_coverage_blocks_missing_duration(self):
        from scripts.shorts_source_clip import _require_audio_coverage
        with self.assertRaisesRegex(RuntimeError, "duration unavailable"):
            _require_audio_coverage([{"codec_type": "audio"}], 32)

    def test_rendered_audio_coverage_accepts_full_track(self):
        from scripts.shorts_source_clip import _require_audio_coverage
        self.assertIsNone(_require_audio_coverage([{"codec_type": "audio", "duration": "32.0"}], 32))


    def test_video_track_shorter_than_audio_blocks(self):
        from scripts.shorts_source_clip import _require_video_coverage
        with self.assertRaisesRegex(RuntimeError, "does not cover full clip"):
            _require_video_coverage([{"codec_type": "video", "duration": "25.0"},
                                     {"codec_type": "audio", "duration": "32.0"}], 32)

    def test_video_track_missing_duration_blocks(self):
        from scripts.shorts_source_clip import _require_video_coverage
        with self.assertRaisesRegex(RuntimeError, "duration unavailable"):
            _require_video_coverage([{"codec_type": "video"}], 32)

    def test_video_track_full_duration_passes(self):
        from scripts.shorts_source_clip import _require_video_coverage
        self.assertIsNone(_require_video_coverage([{"codec_type": "video", "duration": "32.0"}], 32))

    def test_video_track_multiple_streams_blocks(self):
        from scripts.shorts_source_clip import _require_video_coverage
        with self.assertRaisesRegex(RuntimeError, "exactly one video stream"):
            _require_video_coverage([{"codec_type": "video", "duration": "32.0"},
                                     {"codec_type": "video", "duration": "32.0"}], 32)


    def test_ambiguous_or_missing_source_audio_blocks_before_ffmpeg(self):
        # Multi-track sources can put a different language or unlicensed music
        # on 0:a:0; do not silently choose an arbitrary original audio track.
        self.srt.write_text("1\n00:00:00,000 --> 00:00:30,000\nHello world\n")
        self.refresh_caption_hash()
        for audio_count in (0, 2):
            with self.subTest(audio_count=audio_count):
                streams = [{"codec_type": "video", "width": 1920, "height": 1080}]
                streams += [{"codec_type": "audio", "duration": "40.0"} for _ in range(audio_count)]
                probe = {"format": {"duration": "40.0"}, "streams": streams}
                output = self.root / f"no-audio-choice-{audio_count}.mp4"
                with patch("scripts.shorts_source_clip._probe", return_value=probe), \
                     patch("scripts.shorts_source_clip.shutil.which", return_value="/usr/bin/ffmpeg"), \
                     patch("scripts.shorts_source_clip.subprocess.run",
                           side_effect=AssertionError("FFmpeg must not run")):
                    with self.assertRaisesRegex(ValueError, "exactly one unambiguous"):
                        render(self.video, self.srt, self.evidence, output,
                               start=0, seconds=30, language="en")
                self.assertFalse(output.exists())


    def test_multiple_source_video_tracks_block_before_ffmpeg(self):
        self.srt.write_text("1\n00:00:00,000 --> 00:00:30,000\nHello world\n")
        self.refresh_caption_hash()
        streams = [
            {"codec_type": "video", "width": 1920, "height": 1080},
            {"codec_type": "video", "width": 640, "height": 360},
            {"codec_type": "audio", "duration": "40.0"},
        ]
        probe = {"format": {"duration": "40.0"}, "streams": streams}
        output = self.root / "ambiguous-video.mp4"
        with patch("scripts.shorts_source_clip._probe", return_value=probe), \
             patch("scripts.shorts_source_clip.shutil.which", return_value="/usr/bin/ffmpeg"), \
             patch("scripts.shorts_source_clip.subprocess.run",
                   side_effect=AssertionError("FFmpeg must not run")):
            with self.assertRaisesRegex(ValueError, "exactly one unambiguous video track"):
                render(self.video, self.srt, self.evidence, output,
                       start=0, seconds=30, language="en")
        self.assertFalse(output.exists())

    def test_direct_cli_help_without_pythonpath(self):
        import os
        import subprocess
        import sys
        root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run(
            [sys.executable, str(root / "scripts" / "shorts_source_clip.py"), "--help"],
            cwd=root, env=env, capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--duration", result.stdout)


if __name__ == "__main__":
    unittest.main()
