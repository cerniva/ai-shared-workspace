"""HO-20261010-12: keyless MP4 QC evidence measured from real synthetic MP4s.

ffmpeg is a hard requirement (CI installs it with apt); missing ffmpeg is a failure, not a skip.
"""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts import shorts_mp4_qc as qc

ROOT = Path(__file__).resolve().parents[1]


def make(path, video_src, seconds=4, audio=True):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", video_src]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}", "-c:a", "aac"]
    cmd += ["-t", str(seconds), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)]
    subprocess.run(cmd, check=True, timeout=120)
    return path


class ShortsMp4QcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
            raise RuntimeError("ffmpeg/ffprobe are required for MP4 QC tests (apt-get install ffmpeg)")
        cls.tmp = tempfile.TemporaryDirectory()
        d = Path(cls.tmp.name)
        cls.moving = make(d / "moving.mp4", "testsrc2=size=360x640:rate=25")
        cls.black = make(d / "black.mp4", "color=c=black:size=360x640:rate=25")
        cls.still = make(d / "still.mp4", "color=c=0x3366aa:size=360x640:rate=25")
        cls.landscape = make(d / "landscape.mp4", "testsrc2=size=640x360:rate=25")
        cls.silent = make(d / "silent.mp4", "testsrc2=size=360x640:rate=25", audio=False)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_moving_vertical_passes_with_measurements(self):
        r = qc.run_qc(self.moving)
        self.assertTrue(r["pass"], r["blockers"])
        self.assertEqual(r["sha256"], qc.sha256_file(self.moving))
        m = r["measurements"]
        self.assertEqual((m["width"], m["height"]), (360, 640))
        self.assertGreater(m["frames_measured"], 50)
        self.assertGreaterEqual(m["hook_mean_ydif"], qc.MIN_HOOK_YDIF)
        self.assertEqual(qc.verify(self.moving, r), [])

    def test_black_fails(self):
        r = qc.run_qc(self.black)
        self.assertFalse(r["pass"])
        self.assertIn("black_ratio", r["blockers"])
        self.assertIn("moving_footage", r["blockers"])

    def test_still_frame_fails_motion_and_hook(self):
        r = qc.run_qc(self.still)
        self.assertFalse(r["pass"])
        for key in ("freeze_ratio", "moving_footage", "hook_motion_first_3s"):
            self.assertIn(key, r["blockers"])

    def test_landscape_fails(self):
        r = qc.run_qc(self.landscape)
        self.assertEqual(r["blockers"], ["portrait_9_16"])

    def test_missing_audio_fails(self):
        self.assertIn("audio_stream", qc.run_qc(self.silent)["blockers"])

    def test_target_seconds_enforced(self):
        r = qc.run_qc(self.moving, {"target_seconds": 3})
        self.assertIn("duration", r["blockers"])
        self.assertTrue(qc.run_qc(self.moving, {"target_seconds": 30})["pass"])

    def test_sha_mismatch_and_missing_evidence_fail_closed(self):
        r = qc.run_qc(self.moving)
        self.assertIn("mp4_qc_sha256_mismatch", qc.verify(self.landscape, r))
        self.assertEqual(qc.verify(self.moving, None), ["mp4_qc_missing"])
        forged = dict(r, checks={})
        self.assertIn("mp4_qc_check_moving_footage", qc.verify(self.moving, forged))

    def test_unreadable_input_fails_closed(self):
        bad = Path(self.tmp.name) / "bad.mp4"
        bad.write_bytes(b"not an mp4")
        r = qc.run_qc(bad)
        self.assertFalse(r["pass"])
        self.assertTrue(r["blockers"][0].startswith("measurement_failed_"))

    def test_cli_out_and_verify(self):
        out = Path(self.tmp.name) / "qc.json"
        script = str(ROOT / "scripts" / "shorts_mp4_qc.py")
        p = subprocess.run([sys.executable, script, str(self.moving), "--out", str(out)], capture_output=True)
        self.assertEqual(p.returncode, 0)
        self.assertTrue(json.loads(out.read_text())["pass"])
        ok = subprocess.run([sys.executable, script, str(self.moving), "--verify", str(out)], capture_output=True)
        self.assertEqual(ok.returncode, 0)
        bad = subprocess.run([sys.executable, script, str(self.black), "--verify", str(out)], capture_output=True)
        self.assertEqual(bad.returncode, 2)
        missing = subprocess.run([sys.executable, script, str(self.moving), "--verify",
                                  str(out) + ".nope"], capture_output=True)
        self.assertEqual(missing.returncode, 2)


class WorkflowWiringTests(unittest.TestCase):
    def test_build_workflow_runs_qc_before_artifact_upload(self):
        text = (ROOT / ".github/workflows/shorts-free-build.yml").read_text(encoding="utf-8")
        qc_step = text.index("scripts/shorts_mp4_qc.py")
        self.assertLess(text.index("shorts_free_pipeline.py"), qc_step)
        self.assertLess(qc_step, text.index("actions/upload-artifact"))
        self.assertIn("--verify artifacts/mp4_qc.json", text)
        self.assertIn("artifacts/mp4_qc.json", text[text.index("actions/upload-artifact"):])

    def test_orchestration_ci_installs_ffmpeg_and_watches_script(self):
        text = (ROOT / ".github/workflows/worker-orchestration-tests.yml").read_text(encoding="utf-8")
        self.assertIn("apt-get install -y ffmpeg", text)
        self.assertIn("scripts/shorts_mp4_qc.py", text)
        self.assertIn("tests.test_shorts_mp4_qc", text)


if __name__ == "__main__":
    unittest.main()
