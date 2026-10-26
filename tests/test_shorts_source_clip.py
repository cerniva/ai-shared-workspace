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
            "captions_sha256": file_sha256(self.srt),
            "caption_source_url": "https://example.org/test-transcript",
            "caption_license_url": "https://example.org/test-caption-license",
            "caption_license_name": "TEST FIXTURE PERMISSION",
            "caption_attribution_text": "Fixture caption source; test-only attribution",
            "caption_verified_by": "Test fixture only",
            "caption_verified_at": "2026-10-20",
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
        self.data["captions_sha256"] = file_sha256(self.srt)
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

    def test_missing_caption_hash_blocks(self):
        self.data.pop("captions_sha256")
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "captions_sha256"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_same_timing_changed_words_block(self):
        self.srt.write_text("1\n00:00:00,000 --> 00:00:02,000\nChanged words\n\n"
                            "2\n00:00:04,000 --> 00:00:10,000\nAnother sentence\n")
        with self.assertRaisesRegex(ValueError, "captions hash"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_valid_timing_caption_swap_blocks_before_ffmpeg(self):
        import shutil
        self.srt.write_text("1\n00:00:00,000 --> 00:00:30,000\nOriginal approved words\n")
        self.refresh_caption_hash()
        original_copy = shutil.copyfile

        def replace_words_on_copy(src, dst, *args, **kwargs):
            if Path(src) == self.srt:
                self.srt.write_text("1\n00:00:00,000 --> 00:00:30,000\nDifferent unapproved words\n")
            return original_copy(src, dst, *args, **kwargs)

        output = self.root / "changed-words-must-block.mp4"
        with patch("scripts.shorts_source_clip.shutil.copyfile", side_effect=replace_words_on_copy), \
             patch("scripts.shorts_source_clip.shutil.which", return_value="/usr/bin/ffmpeg"), \
             patch("scripts.shorts_source_clip.subprocess.run",
                   side_effect=AssertionError("FFmpeg must not run")):
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

    def test_missing_caption_license_blocks_before_render(self):
        self.data.pop("caption_license_url")
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "caption_license_url"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_missing_caption_attribution_blocks(self):
        self.data.pop("caption_attribution_text")
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "caption_attribution_text"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_unapproved_caption_derivatives_block(self):
        self.data["caption_derivatives_permitted"] = False
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "caption_derivatives_permitted"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_caption_license_requires_https(self):
        self.data["caption_license_url"] = "http://example.org/insecure"
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "caption_license_url must be an HTTPS URL"):
            validate_rights(self.video, self.srt, self.evidence, "en")

    def test_caption_license_provenance_present(self):
        evidence = validate_rights(self.video, self.srt, self.evidence, "en")
        self.assertEqual(evidence["caption_license_name"], "TEST FIXTURE PERMISSION")

    def test_hash_mismatch_blocks(self):
        self.data["source_sha256"] = "0" * 64
        self.evidence.write_text(json.dumps(self.data))
        with self.assertRaisesRegex(ValueError, "hash"):
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

    def test_portrait_filter_fills_frame_without_letterboxing(self):
        from scripts.shorts_source_clip import _portrait_filter
        vf = _portrait_filter(0.5, 0.5)
        self.assertIn("force_original_aspect_ratio=increase", vf)
        self.assertIn("crop=1080:1920:", vf)
        self.assertNotIn("pad=", vf)
        self.assertIn("subtitles=captions.srt", vf)

    def test_non_square_pixel_source_preserves_displayed_subject_shape(self):
        # A 150x200 sample rectangle with SAR=4/3 is square on display.
        # Render the real FFmpeg crop chain and ensure it stays square.
        import shutil
        import subprocess
        from scripts.shorts_source_clip import _portrait_filter

        if not shutil.which("ffmpeg"):
            self.skipTest("FFmpeg unavailable")
        filt = _portrait_filter(0.5, 0.5).replace(",subtitles=captions.srt", "")
        source = ("color=c=black:s=1440x1080:r=1,"
                  "drawbox=x=600:y=440:w=150:h=200:color=white:t=fill,"
                  "setsar=4/3")
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error",
                   "-f", "lavfi", "-i", source, "-vf", filt,
                   "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
        result = subprocess.run(command, capture_output=True, timeout=45, check=True)
        self.assertEqual(len(result.stdout), 1080 * 1920)
        white = [i for i, value in enumerate(result.stdout) if value > 240]
        self.assertTrue(white, "synthetic subject missing after crop")
        left = min(i % 1080 for i in white)
        right = max(i % 1080 for i in white)
        top = min(i // 1080 for i in white)
        bottom = max(i // 1080 for i in white)
        self.assertLessEqual(abs((right - left) - (bottom - top)), 3)

    def test_portrait_crop_anchors_are_explicit(self):
        from scripts.shorts_source_clip import _portrait_filter
        vf = _portrait_filter(0.0, 1.0)
        self.assertIn("(iw-1080)*0.000:(ih-1920)*1.000", vf)

    def test_invalid_crop_coordinates_fail_closed_before_ffmpeg(self):
        for value in (-0.01, 1.01, float("nan"), float("inf")):
            with self.subTest(value=value):
                output = self.root / "must-not-exist.mp4"
                with patch("scripts.shorts_source_clip.subprocess.run",
                           side_effect=AssertionError("FFmpeg must not run")):
                    with self.assertRaisesRegex(ValueError, "crop_x and crop_y"):
                        render(self.video, self.srt, self.evidence, output,
                               start=0, seconds=30, language="en", crop_x=value)
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
