"""shorts_free_pipeline must consume plan_learnings.json and record applied learning ids."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import shorts_free_pipeline as pipeline
from scripts import shorts_learnings as sl
from scripts.plan_learnings import plan_learnings
from tests.test_shorts_free_pipeline import asset, fake_download, valid_packet

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [sl.PRIVACY, sl.QUOTA, sl.CERNO, sl.HO04_GATE]


def doc(ids=REQUIRED, tag="video_shopify", error=None):
    return {"tag": tag, "count": len(ids), "error": error,
            "learnings": [{"learning_id": i, "title": i, "decision": "d", "source_ids": []} for i in ids]}


class ShortsLearningsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _files(self, learnings, packet=None):
        lp = self.base / "plan_learnings.json"
        lp.write_text(json.dumps(learnings))
        pp = self.base / "packet.json"
        pp.write_text(json.dumps(packet or valid_packet()))
        return pp, lp

    def _run(self, learnings, packet=None):
        pp, lp = self._files(learnings, packet)
        with patch.object(pipeline, "search_free_media", return_value=[asset("pexels", "a")]) as search, \
             patch.object(pipeline, "download_asset", side_effect=fake_download), \
             patch.object(pipeline, "_probe_real_video", return_value=None):
            result = pipeline.prepare_render_bundle(pp, self.base / "work", env={}, learnings_path=lp)
        return result, search

    def test_real_ledger_has_every_required_learning(self):
        ids = {row["learning_id"] for row in plan_learnings("video_shopify")["learnings"]}
        self.assertTrue(set(REQUIRED) <= ids, sorted(set(REQUIRED) - ids))

    def test_learnings_applied_and_recorded(self):
        result, _ = self._run(doc())
        manifest = json.loads(Path(result["render_manifest"]).read_text())
        self.assertEqual(result["applied_learning_ids"], REQUIRED)
        self.assertEqual(manifest["applied_learning_ids"], REQUIRED)
        policy = manifest["upload_policy"]
        self.assertEqual(policy["privacyStatus"], "private")
        self.assertIs(policy["selfDeclaredMadeForKids"], False)
        self.assertIs(policy["containsSyntheticMedia"], True)
        self.assertEqual(policy["quota"]["daily_uploads"], 100)
        self.assertEqual(policy["quota"]["reset"], "00:00 America/Los_Angeles")
        gates = manifest["production_gates"]
        for key in ("moving_footage_only", "hook_storyboard_qc_required", "rights_qc_required", "full_mp4_qc_required"):
            self.assertIs(gates[key], True)

    def test_missing_required_learning_fails_before_media_fetch(self):
        with self.assertRaisesRegex(ValueError, "bridge_failure: required learnings missing: " + sl.QUOTA):
            self._run(doc([i for i in REQUIRED if i != sl.QUOTA]))

    def test_missing_errored_or_wrong_tag_file_fails(self):
        pp, _ = self._files(doc())
        with self.assertRaisesRegex(ValueError, "file missing"):
            pipeline.prepare_render_bundle(pp, self.base / "w", env={}, learnings_path=self.base / "nope.json")
        for bad in (doc(error="ledger broken"), doc(tag="finance")):
            with self.assertRaisesRegex(ValueError, "bridge_failure"):
                self._run(bad)

    def test_cerno_30s_cap_and_broadcast_clips_block_without_search(self):
        packet = valid_packet(); packet["target_seconds"] = 45
        with self.assertRaisesRegex(ValueError, "max 30s"):
            pp, lp = self._files(doc(), packet)
            with patch.object(pipeline, "search_free_media") as search:
                pipeline.prepare_render_bundle(pp, self.base / "w", env={}, learnings_path=lp)
        search.assert_not_called()
        packet = valid_packet(); packet["uses_broadcast_clips"] = True
        with self.assertRaisesRegex(ValueError, "broadcast"):
            self._run(doc(), packet)

    def test_cli_requires_learnings_and_reports_bridge_failure(self):
        pp, _ = self._files(doc())
        script = ROOT / "scripts" / "shorts_free_pipeline.py"
        no_flag = subprocess.run([sys.executable, str(script), str(pp), str(self.base / "w"), str(self.base / "o.mp4")],
                                 capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(no_flag.returncode, 2)
        self.assertIn("--learnings", no_flag.stderr)
        missing = subprocess.run([sys.executable, str(script), str(pp), str(self.base / "w"), str(self.base / "o.mp4"),
                                  "--learnings", str(self.base / "nope.json")], capture_output=True, text=True, cwd=ROOT)
        self.assertEqual(missing.returncode, 2)
        self.assertIn("bridge_failure", json.loads(missing.stdout)["error"])

    def test_workflow_passes_learnings_to_pipeline(self):
        text = (ROOT / ".github" / "workflows" / "shorts-free-build.yml").read_text()
        self.assertIn("--learnings artifacts/plan_learnings.json", text)


if __name__ == "__main__":
    unittest.main()
