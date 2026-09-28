import json
import math
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.shorts_render import render, validate_spec


def run(args):
    return subprocess.run(args, capture_output=True, text=True, check=True, timeout=120)


def write_tone(path: Path, seconds: float = 1.4, rate: int = 44100):
    frames = int(seconds * rate)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        for i in range(frames):
            sample = int(8000 * math.sin(2 * math.pi * 440 * i / rate))
            wav.writeframesraw(struct.pack("<h", sample))


def write_ppm(path: Path):
    path.write_bytes(b"P6\n2 2\n255\n" + bytes([255, 0, 0] * 4))


class ShortsRenderTests(unittest.TestCase):
    def test_validate_spec_requires_at_least_one_visual(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            narration = base / "voice.wav"
            write_tone(narration, 0.2)
            with self.assertRaisesRegex(ValueError, "visual"):
                validate_spec({"visuals": [], "narration": "voice.wav"}, base)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
    def test_render_creates_portrait_h264_aac_mp4_from_free_local_media(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            image = base / "frame.ppm"
            clip = base / "clip.mp4"
            narration = base / "voice.wav"
            music = base / "music.wav"
            subtitles = base / "captions.srt"
            manifest = base / "render.json"
            output = base / "short.mp4"

            write_ppm(image)
            write_tone(narration, 1.4)
            write_tone(music, 1.4)
            subtitles.write_text("1\n00:00:00,000 --> 00:00:01,200\nFREE RENDER TEST\n", encoding="utf-8")
            run([
                "ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=blue:s=640x360:d=0.7",
                "-vf", "fps=30", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip),
            ])
            manifest.write_text(json.dumps({
                "target_seconds": 1.2,
                "visuals": [
                    {"path": "frame.ppm", "duration": 0.6},
                    {"path": "clip.mp4", "duration": 0.6},
                ],
                "narration": "voice.wav",
                "music": "music.wav",
                "music_volume": 0.08,
                "subtitles": "captions.srt",
            }), encoding="utf-8")

            result = render(manifest, output)
            self.assertEqual(result["output"], str(output.resolve()))
            self.assertTrue(output.is_file())
            self.assertGreater(output.stat().st_size, 1000)

            probe = json.loads(run([
                "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(output)
            ]).stdout)
            video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
            audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
            self.assertEqual(video["codec_name"], "h264")
            self.assertEqual((video["width"], video["height"]), (1080, 1920))
            self.assertEqual(audio["codec_name"], "aac")
            self.assertGreater(float(probe["format"]["duration"]), 1.0)


if __name__ == "__main__":
    unittest.main()
