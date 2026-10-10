import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import shorts_render


def norm(engine="edge-tts", voice="tr-TR-AhmetNeural", fallback="tr"):
    return {
        "narration_text": "Merhaba dünya.",
        "narration_voice": voice,
        "narration_engine": engine,
        "narration_fallback_voice": fallback,
        "narration_speed": 165,
    }


class EdgeTtsTests(unittest.TestCase):
    def test_validate_rejects_unknown_engine(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "f.ppm").write_bytes(b"P6\n2 2\n255\n" + bytes(12))
            spec = {"visuals": [{"path": "f.ppm", "duration": 1}], "narration_text": "x",
                    "narration_engine": "paid-cloud"}
            with self.assertRaises(ValueError):
                shorts_render.validate_spec(spec, base)

    def test_validate_defaults_to_espeak(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            (base / "f.ppm").write_bytes(b"P6\n2 2\n255\n" + bytes(12))
            spec = {"visuals": [{"path": "f.ppm", "duration": 1}], "narration_text": "x"}
            with mock.patch.dict("os.environ", {}, clear=True):
                self.assertEqual(shorts_render.validate_spec(spec, base)["narration_engine"], "espeak")

    def test_edge_rate_mapping(self):
        self.assertEqual(shorts_render._edge_rate(165), "+0%")
        self.assertEqual(shorts_render._edge_rate(198), "+20%")
        self.assertEqual(shorts_render._edge_rate(10), "-50%")

    def test_edge_success_reports_engine(self):
        with mock.patch.object(shorts_render, "_synthesize_edge") as edge, \
             mock.patch.object(shorts_render, "_synthesize_narration") as esp:
            info = shorts_render.synthesize_with_fallback(norm(), Path("/tmp/x.wav"))
        edge.assert_called_once()
        esp.assert_not_called()
        self.assertEqual(info["engine"], "edge-tts")
        self.assertEqual(info["voice"], "tr-TR-AhmetNeural")

    def test_edge_failure_falls_back_to_espeak_voice(self):
        with mock.patch.object(shorts_render, "_synthesize_edge", side_effect=RuntimeError("offline")), \
             mock.patch.object(shorts_render.shutil, "which", return_value="/usr/bin/espeak-ng"), \
             mock.patch.object(shorts_render, "_synthesize_narration") as esp:
            info = shorts_render.synthesize_with_fallback(norm(), Path("/tmp/x.wav"))
        esp.assert_called_once_with("Merhaba dünya.", "tr", 165, Path("/tmp/x.wav"))
        self.assertEqual(info["engine"], "espeak")
        self.assertIn("offline", info["fallback_errors"][0])

    def test_espeak_engine_never_calls_edge(self):
        with mock.patch.object(shorts_render, "_synthesize_edge") as edge, \
             mock.patch.object(shorts_render.shutil, "which", return_value="/usr/bin/espeak-ng"), \
             mock.patch.object(shorts_render, "_synthesize_narration"):
            info = shorts_render.synthesize_with_fallback(norm("espeak", "tr", None), Path("/tmp/x.wav"))
        edge.assert_not_called()
        self.assertEqual(info["voice"], "tr")

    def _spec_dir(self, td):
        base = Path(td)
        (base / "f.ppm").write_bytes(b"P6\n2 2\n255\n" + bytes(12))
        return base

    def test_env_opt_in_maps_espeak_voice_to_neural(self):
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict("os.environ", {"SHORTS_TTS_ENGINE": "edge-tts"}):
            spec = {"visuals": [{"path": "f.ppm", "duration": 1}], "narration_text": "x",
                    "narration_voice": "tr"}
            n = shorts_render.validate_spec(spec, self._spec_dir(td))
        self.assertEqual(n["narration_engine"], "edge-tts")
        self.assertEqual(n["narration_voice"], "tr-TR-AhmetNeural")
        self.assertEqual(n["narration_fallback_voice"], "tr")

    def test_env_opt_in_keeps_unknown_voice_on_espeak(self):
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict("os.environ", {"SHORTS_TTS_ENGINE": "edge-tts"}):
            spec = {"visuals": [{"path": "f.ppm", "duration": 1}], "narration_text": "x",
                    "narration_voice": "de"}
            n = shorts_render.validate_spec(spec, self._spec_dir(td))
        self.assertEqual(n["narration_engine"], "espeak")
        self.assertEqual(n["narration_voice"], "de")

    @unittest.skipUnless(shutil.which("edge-tts") and shutil.which("ffmpeg"), "edge-tts/ffmpeg required")
    def test_edge_live_turkish(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "n.wav"
            try:
                shorts_render._synthesize_edge("Soğan.", "tr-TR-AhmetNeural", 165, out)
            except RuntimeError as exc:
                self.skipTest(f"edge-tts network unavailable: {exc}")
            self.assertGreater(out.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
