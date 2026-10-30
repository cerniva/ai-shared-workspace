"""Synthetic, rights-neutral technical tests only; no sourced media or uploads."""
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.shorts_multisegment_preflight import build_concat_graph, validate_segments


class MultiSegmentPreflightTests(unittest.TestCase):
    def test_nomiku_candidate_b_duration(self):
        cuts = [(0, 15.4), (58, 79.1)]
        self.assertEqual(validate_segments(cuts, 84.49), 36.5)
        graph = build_concat_graph(cuts, 84.49)
        self.assertIn("atrim=start=58.000:end=79.100", graph)
        self.assertIn("concat=n=2:v=1:a=1[vcat][acat]", graph)
        self.assertNotIn("anullsrc", graph)
        self.assertNotIn("sine", graph)

    def test_rejects_overlap_reverse_nan_and_out_of_bounds(self):
        cases = [([(0, 20), (19, 40)], 84), ([(30, 20)], 84),
                 ([(0, float('nan'))], 84), ([(0, 36)], 30),
                 ([(0, 20)], 84), ([(0, 15), (58, 90)], 84)]
        for cuts, duration in cases:
            with self.subTest(cuts=cuts), self.assertRaises(ValueError):
                validate_segments(cuts, duration)

    def test_rejects_boolean_timestamps_and_source_duration(self):
        for cuts, duration in [([(False, 35)], 84), ([(0, True)], 84),
                               ([(0, 35)], True), ([(0, 35)], False)]:
            with self.subTest(cuts=cuts, duration=duration), self.assertRaises(ValueError):
                build_concat_graph(cuts, duration)

    def test_rejects_submillisecond_cuts_lost_in_ffmpeg_graph(self):
        with self.assertRaisesRegex(ValueError, "millisecond"):
            build_concat_graph([(0, 0.0004), (5, 39.9996)], 50)

    def test_synthetic_ffmpeg_preserves_two_audio_and_video_sections(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("free FFmpeg/ffprobe not installed")
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "synthetic.mp4"
            out = Path(tmp) / "concatenated.mp4"
            generate = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                        "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=15",
                        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000",
                        "-t", "6", "-c:v", "libx264", "-preset", "ultrafast",
                        "-pix_fmt", "yuv420p", "-c:a", "aac", str(src)]
            subprocess.run(generate, check=True, capture_output=True, timeout=60)
            graph = build_concat_graph([(0, 2), (4, 6)], 6, enforce_shorts=False)
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(src),
                   "-filter_complex", graph, "-map", "[vcat]", "-map", "[acat]",
                   "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                   "-c:a", "aac", str(out)]
            subprocess.run(cmd, check=True, capture_output=True, timeout=60)
            p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration:stream=codec_type,duration,start_time",
                                "-of", "json", str(out)], check=True, capture_output=True, text=True)
            info = json.loads(p.stdout)
            self.assertAlmostEqual(float(info["format"]["duration"]), 4.0, delta=0.2)
            self.assertEqual([s["codec_type"] for s in info["streams"]], ["video", "audio"])
            for stream in info["streams"]:
                self.assertGreaterEqual(float(stream["duration"]), 3.7)
                self.assertLess(abs(float(stream["start_time"])), 0.15)


if __name__ == "__main__":
    unittest.main()
