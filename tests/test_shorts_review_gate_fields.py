"""hook_storyboard_checked / moving_footage_checked review fields (ChatGPT spec da6bdc4).

Both are required independent review checks when the render manifest turns on the
hook_storyboard / moving_footage production gates. Missing, false or non-boolean
values must keep preflight ready=false and must block the upload path.
"""
import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts import shorts_preflight as pf
from scripts import youtube_upload as yu

BASE_REQUIRED = ["speech_intelligible", "audio_visual_sync", "text_readable",
                 "facts_verified", "rights_checked", "correct_channel", "duplicate_checked"]
GATES = {"hook_storyboard_qc_required": True, "rights_qc_required": True,
         "full_mp4_qc_required": True, "moving_footage_only": True}
MANIFEST = {"production_gates": GATES}


def full_checks(**override):
    checks = {k: True for k in BASE_REQUIRED}
    checks.update(hook_storyboard_checked=True, moving_footage_checked=True)
    checks.update(override)
    return {k: v for k, v in checks.items() if v is not ...}


class ReviewGateFieldUnitTests(unittest.TestCase):
    def test_fields_are_mapped_to_hook_storyboard_and_moving_footage_gates(self):
        self.assertEqual(pf.REVIEW_GATE_FIELDS["hook_storyboard_checked"], "hook_storyboard_qc_required")
        self.assertEqual(pf.REVIEW_GATE_FIELDS["moving_footage_checked"], "moving_footage_only")
        self.assertIn("hook_storyboard_checked", pf.MANIFEST_GATE_REVIEW_CHECKS["hook_storyboard_qc_required"])
        self.assertIn("moving_footage_checked", pf.MANIFEST_GATE_REVIEW_CHECKS["moving_footage_only"])

    def test_missing_fields_block_with_clear_reason(self):
        review = {"sha256": "x", "reviewer": "qc", "checks": full_checks(
            hook_storyboard_checked=..., moving_footage_checked=...)}
        blockers = pf.manifest_gate_blockers(MANIFEST, review)
        self.assertIn("review_hook_storyboard_checked_missing", blockers)
        self.assertIn("review_moving_footage_checked_missing", blockers)

    def test_false_fields_block_with_clear_reason(self):
        review = {"sha256": "x", "reviewer": "qc", "checks": full_checks(
            hook_storyboard_checked=False, moving_footage_checked=False)}
        blockers = pf.manifest_gate_blockers(MANIFEST, review)
        self.assertIn("review_hook_storyboard_checked_false", blockers)
        self.assertIn("review_moving_footage_checked_false", blockers)

    def test_null_and_string_are_not_evidence(self):
        review = {"checks": {"hook_storyboard_checked": None, "moving_footage_checked": "true"}}
        self.assertEqual(pf.review_gate_evidence(MANIFEST, review),
                         {"hook_storyboard_checked": "missing", "moving_footage_checked": "not_boolean"})

    def test_only_enabled_gates_require_their_field(self):
        manifest = {"production_gates": {"moving_footage_only": True, "hook_storyboard_qc_required": False}}
        self.assertEqual(pf.review_gate_evidence(manifest, None), {"moving_footage_checked": "missing"})
        self.assertEqual(pf.review_gate_evidence(None, None), {})

    def test_both_true_pass(self):
        review = {"sha256": "x", "reviewer": "qc", "checks": full_checks()}
        self.assertEqual(pf.manifest_gate_blockers(MANIFEST, review), [])


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg required")
class ReviewGateFieldEndToEndTests(unittest.TestCase):
    """Real MP4 through inspect() and the upload gate."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.video = Path(cls.tmp.name) / "short.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y",
                        "-f", "lavfi", "-i", "testsrc=size=360x640:rate=25:duration=2",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=2",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest",
                        str(cls.video)], check=True, timeout=120)
        cls.sha = hashlib.sha256(cls.video.read_bytes()).hexdigest()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def review(self, **override):
        return {"sha256": self.sha, "reviewer": "independent-qc", "checks": full_checks(**override)}

    def write(self, report):
        path = Path(self.tmp.name) / "preflight.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        return path

    def test_positive_independent_review_with_both_fields_is_ready_and_uploadable(self):
        report = pf.inspect(self.video, self.review(), MANIFEST)
        self.assertEqual(report["blockers"], [])
        self.assertTrue(report["ready"])
        self.assertTrue(report["manifest_gates_checked"])
        self.assertEqual(report["review_gate_evidence"],
                         {"hook_storyboard_checked": "true", "moving_footage_checked": "true"})
        yu.require_ready_preflight(self.video, self.write(report))

    def test_missing_hook_storyboard_checked_blocks_ready(self):
        report = pf.inspect(self.video, self.review(hook_storyboard_checked=...), MANIFEST)
        self.assertFalse(report["ready"])
        self.assertIn("review_hook_storyboard_checked_missing", report["blockers"])

    def test_false_moving_footage_checked_blocks_ready(self):
        report = pf.inspect(self.video, self.review(moving_footage_checked=False), MANIFEST)
        self.assertFalse(report["ready"])
        self.assertIn("review_moving_footage_checked_false", report["blockers"])

    def test_upload_fails_closed_without_manifest(self):
        report = pf.inspect(self.video, self.review(), None)
        self.assertTrue(report["ready"])  # legacy CLI still works for technical use
        self.assertFalse(report["manifest_gates_checked"])
        with self.assertRaisesRegex(ValueError, "--manifest"):
            yu.require_ready_preflight(self.video, self.write(report))

    def test_upload_rejects_forged_ready_without_review_fields(self):
        report = pf.inspect(self.video, self.review(), MANIFEST)
        report["review_gate_evidence"] = {"hook_storyboard_checked": "true"}
        with self.assertRaisesRegex(ValueError, "moving_footage_checked"):
            yu.require_ready_preflight(self.video, self.write(report))


class WorkflowManifestWiringTests(unittest.TestCase):
    ROOT = Path(__file__).resolve().parents[1] / ".github" / "workflows"

    def test_build_and_smoke_pass_render_manifest_and_require_gate_check(self):
        for name in ("shorts-free-build.yml", "shorts-free-smoke-once.yml"):
            text = (self.ROOT / name).read_text(encoding="utf-8")
            self.assertIn("--manifest artifacts/bundle/render.json", text, name)
            self.assertIn("manifest_gates_not_checked", text, name)

    def test_render_workflow_passes_manifest_when_it_has_gates(self):
        text = (self.ROOT / "shorts-free-render.yml").read_text(encoding="utf-8")
        self.assertIn('manifest_args=(--manifest "$MANIFEST")', text)
        self.assertIn('"${manifest_args[@]}"', text)
