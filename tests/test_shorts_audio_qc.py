"""Fail-closed audio activity regression tests; no licensed media needed."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from scripts.shorts_audio_qc import inspect


class AudioQCTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "fixture.mp4"
        self.path.write_bytes(b"unit-test fixture, not real video")

    def check(self, log):
        probe = SimpleNamespace(returncode=0, stdout=json.dumps({
            "format": {"duration": "30.0"},
            "streams": [{"codec_type": "audio", "duration": "30.0"}],
        }), stderr="")
        decode = SimpleNamespace(returncode=0, stdout="", stderr=log)
        with patch("scripts.shorts_audio_qc.subprocess.run", side_effect=[probe, decode]):
            return inspect(self.path)

    def test_full_silence_is_blocked(self):
        result = self.check("[silencedetect] silence_start: 0\n[silencedetect] silence_end: 30 | silence_duration: 30")
        self.assertEqual(result["audio_qc"], "QC_BLOCKED")
        self.assertEqual(result["silence_fraction"], 1.0)

    def test_28_seconds_silent_is_blocked(self):
        result = self.check("[silencedetect] silence_start: 0\n[silencedetect] silence_end: 28 | silence_duration: 28")
        self.assertEqual(result["audio_qc"], "QC_BLOCKED")
        self.assertGreater(result["silence_fraction"], 0.9)

    def test_active_audio_is_technical_only(self):
        result = self.check("")
        self.assertEqual(result["audio_qc"], "PASS_TECHNICAL_ONLY")
        self.assertFalse(result["publish_ready"])

    def test_missing_file_is_blocked(self):
        with self.assertRaises(ValueError):
            inspect(self.path.parent / "missing.mp4")


if __name__ == "__main__":
    unittest.main()
