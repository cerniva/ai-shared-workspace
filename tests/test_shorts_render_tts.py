import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.shorts_render import render, validate_spec


def run(args):
    """Run a subprocess for integration assertions and return its completed result."""
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=120)


def write_ppm(path: Path):
    """Write a tiny deterministic PPM frame for renderer tests."""
    path.write_bytes(b"P6\n2 2\n255\n" + bytes([40, 80, 180] * 4))


class ShortsRenderTtsTests(unittest.TestCase):
    def test_validate_spec_accepts_text_narration_without_audio_file(self):
        """Accept text narration as a zero-credit alternative to an audio file."""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            image = base / "frame.ppm"
            write_ppm(image)
            spec = {
                "target_seconds": 1.2,
                "visuals": [{"path": "frame.ppm", "duration": 1.2}],
                "narration_text": "This is a zero-credit narration test.",
                "narration_voice": "en-us",
            }
            normalized = validate_spec(spec, base)
            self.assertEqual(normalized["narration_text"], spec["narration_text"])
            self.assertIsNone(normalized["narration"])

    @unittest.skipUnless(
        shutil.which("ffmpeg") and shutil.which("ffprobe") and shutil.which("espeak-ng"),
        "ffmpeg/ffprobe/espeak-ng required",
    )
    def test_render_creates_audible_mp4_from_text_narration(self):
        """Render text narration into an MP4 with a detectable AAC audio stream."""
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            image = base / "frame.ppm"
            manifest = base / "render.json"
            output = base / "short.mp4"
            write_ppm(image)
            manifest.write_text(
                json.dumps({
                    "target_seconds": 1.5,
                    "visuals": [{"path": "frame.ppm", "duration": 1.5}],
                    "narration_text": "Free narration is working.",
                    "narration_voice": "en-us",
                    "narration_speed": 165,
                }),
                encoding="utf-8",
            )

            result = render(manifest, output)
            self.assertEqual(result["credits_spent"], 0)
            data = json.loads(run([
                "ffprobe", "-v", "error", "-show_streams", "-of", "json", str(output)
            ]).stdout)
            audio = next(s for s in data["streams"] if s["codec_type"] == "audio")
            self.assertEqual(audio["codec_name"], "aac")

            volume = run([
                "ffmpeg", "-hide_banner", "-i", str(output), "-map", "0:a:0",
                "-af", "volumedetect", "-vn", "-f", "null", "-"
            ]).stderr
            self.assertIn("mean_volume", volume)


if __name__ == "__main__":
    unittest.main()
