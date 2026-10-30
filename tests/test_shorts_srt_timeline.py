"""No external network, real media, or publication in these preflight tests."""
import hashlib
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from scripts.shorts_srt_timeline import audit, main, parse_stamp, read_cues

SOURCE_TIMES = [(0, 8), (10, 15), (16, 24), (25, 28), (29, 35),
                (37, 48), (49, 57), (58, 64), (65, 71), (72, 79), (80, 84)]


def fixture(times=SOURCE_TIMES):
    return "\n\n".join(f"{i}\n00:{s//60:02}:{s%60:02} --> 00:{e//60:02}:{e%60:02}\n" + ("A" * (60 if i == 1 else 20))
                       for i, (s, e) in enumerate(times, 1)) + "\n"


class TimelineTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "source.srt"
        self.path.write_text(fixture(), encoding="utf-8")
        self.sha = hashlib.sha256(self.path.read_bytes()).hexdigest()

    def test_nomiku_two_segment_mapping(self):
        r = audit(self.path, self.sha, [(0, 28.4), (65, 71.4)])
        self.assertEqual(r["duration"], 34.8)
        self.assertEqual([x["cue"] for x in r["mapped_cues"]], [1, 2, 3, 4, 9])
        self.assertEqual((r["mapped_cues"][-1]["short_start"], r["mapped_cues"][-1]["short_end"]), (28.4, 34.4))
        self.assertEqual(r["boundary_crossing_cues"], [])
        self.assertEqual(r["mobile_readability_review_cues"], [1])
        self.assertTrue(r["caption_format_conversion_required"])
        self.assertEqual(r["technical_preflight_gate"], "BLOCKED")
        self.assertIn("SRT_MILLISECONDS_REQUIRED", r["technical_preflight_blockers"])
        self.assertIn("MOBILE_READABILITY_REVIEW", r["technical_preflight_blockers"])
        self.assertFalse(r["publish_ready"])

    def test_cut_inside_cue_blocks(self):
        r = audit(self.path, self.sha, [(0, 27), (65, 72)])
        self.assertEqual(r["boundary_crossing_cues"], [4])
        self.assertEqual(r["timeline_boundary_gate"], "BLOCKED")

    def test_wrong_hash_blocks(self):
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            audit(self.path, "0" * 64, [(0, 28.4), (65, 71.4)])

    def test_duration_gate(self):
        with self.assertRaisesRegex(ValueError, "30-40"):
            audit(self.path, self.sha, [(0, 20)])

    def test_invalid_time_and_overlap(self):
        with self.assertRaises(ValueError):
            parse_stamp("00:60:00")
        with self.assertRaisesRegex(ValueError, "overlapping"):
            read_cues(fixture([(0, 8), (7, 10)]))

    def test_overlapping_segments_block(self):
        with self.assertRaisesRegex(ValueError, "ordered and non-overlapping"):
            audit(self.path, self.sha, [(0, 28.4), (25, 31)])

    def test_fractional_srt(self):
        self.assertEqual(parse_stamp("00:00:01,250"), 1.25)
        self.assertEqual(parse_stamp("00:00:01.250"), 1.25)

    def test_valid_millisecond_srt_can_pass_technical_preflight(self):
        self.path.write_text("1\\n00:00:00,000 --> 00:00:32,000\\nHello\\n".replace("\\n", "\n"), encoding="utf-8")
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        report = audit(self.path, digest, [(0, 32)])
        self.assertEqual(report["technical_preflight_gate"], "PASS_TECHNICAL_ONLY")
        self.assertEqual(report["technical_preflight_blockers"], [])
        self.assertFalse(report["publish_ready"])

    def test_cli_exits_nonzero_for_whole_second_and_overlong_srt(self):
        argv = ["shorts_srt_timeline.py", "--srt", str(self.path),
                "--expected-sha256", self.sha, "--segment", "0:28.4",
                "--segment", "65:71.4"]
        output = io.StringIO()
        with mock.patch("sys.argv", argv), redirect_stdout(output):
            code = main()
        self.assertEqual(code, 2)
        report = json.loads(output.getvalue())
        self.assertFalse(report["ok"])
        self.assertEqual(report["timeline_boundary_gate"], "PASS_TECHNICAL_ONLY")
        self.assertEqual(report["technical_preflight_gate"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
