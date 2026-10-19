"""Fail-closed tests for preserving sourced footage/audio; no network or YouTube."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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
            "reuse_permitted": True,
            "derivatives_permitted": True,
            "audio_reuse_permitted": True,
            "verified_at": "2026-10-20",
            "verified_by": "Test fixture only",
            "spoken_language": "en",
            "caption_language": "en",
        }
        self.evidence.write_text(json.dumps(self.data))

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


if __name__ == "__main__":
    unittest.main()
