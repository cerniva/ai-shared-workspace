import hashlib
import contextlib
import json
import os
import subprocess
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.verify_render_artifact import LEARNING_ID, SOURCE_ID, active_rule, verify_and_extract, main


def zipped(items):
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        for name, data in items.items():
            z.writestr(name, data)
    return out.getvalue()


class DigestConsumerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.zip_path = self.root / "render.zip"
        self.zip_path.write_bytes(zipped({
            "short.mp4": b"video", "preflight.json": b"{}",
            "bundle/render.json": b"{}",
        }))
        self.digest = "sha256:" + hashlib.sha256(self.zip_path.read_bytes()).hexdigest()

    def test_positive_digest_changes_decision_and_readback(self):
        target = self.root / "render"
        verify_and_extract(self.zip_path, self.digest, target)
        self.assertEqual((target / "short.mp4").read_bytes(), b"video")
        self.assertEqual((target / "bundle/render.json").read_text(), "{}")

    def test_mismatch_fails_closed_without_artifact(self):
        target = self.root / "render"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            verify_and_extract(self.zip_path, "sha256:" + "0" * 64, target)
        self.assertFalse(target.exists())

    def test_missing_digest_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "digest missing"):
            verify_and_extract(self.zip_path, "", self.root / "render")

    def test_unsafe_zip_fails_closed(self):
        self.zip_path.write_bytes(zipped({
            "../evil": b"no", "preflight.json": b"{}",
            "bundle/render.json": b"{}",
        }))
        digest = "sha256:" + hashlib.sha256(self.zip_path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError, "unsafe"):
            verify_and_extract(self.zip_path, digest, self.root / "render")
        self.assertFalse((self.root / "evil").exists())

    def test_missing_learning_fails_closed(self):
        with patch("scripts.verify_render_artifact.LearningLedger") as ledger:
            ledger.return_value.for_plan.return_value = []
            with self.assertRaisesRegex(ValueError, "learning missing"):
                active_rule()

    def test_inactive_learning_fails_closed(self):
        with patch("scripts.verify_render_artifact.LearningLedger") as ledger:
            ledger.return_value.for_plan.return_value = [{
                "learning_id": LEARNING_ID, "status": "inactive",
                "source_ids": [SOURCE_ID],
            }]
            with self.assertRaisesRegex(ValueError, "learning missing"):
                active_rule()

    def test_superseded_learning_fails_closed(self):
        with patch("scripts.verify_render_artifact.LearningLedger") as ledger:
            ledger.return_value.for_plan.return_value = [{
                "learning_id": LEARNING_ID, "status": "superseded",
                "source_ids": [SOURCE_ID],
            }]
            with self.assertRaisesRegex(ValueError, "learning missing"):
                active_rule()

    def test_active_learning_requires_official_source(self):
        row = {
            "learning_id": LEARNING_ID, "source_ids": [SOURCE_ID],
            "decision": "digest mismatch must fail",
        }
        with patch("scripts.verify_render_artifact.LearningLedger") as ledger, \
             patch("scripts.verify_render_artifact.SourceCatalog") as catalog:
            ledger.return_value.for_plan.return_value = [row]
            catalog.return_value.find.return_value = {"evidence_tier": "official"}
            self.assertEqual(active_rule()["learning_id"], LEARNING_ID)
            catalog.return_value.find.return_value = {"evidence_tier": "unverified"}
            with self.assertRaisesRegex(ValueError, "official"):
                active_rule()


    def test_failed_download_never_logs_secret_or_applies_learning(self):
        stderr = io.StringIO()
        report = self.root / "report.json"
        artifact = {
            "id": 17, "digest": self.digest,
            "archive_download_url": "https://api.github.com/repos/cerniva/ai-shared-workspace/actions/artifacts/17/zip",
        }
        with patch("scripts.verify_render_artifact.active_rule", return_value={
            "learning_id": LEARNING_ID, "source_ids": [SOURCE_ID],
        }), patch("scripts.verify_render_artifact.fetch_metadata", return_value=artifact), \
             patch("scripts.verify_render_artifact.subprocess.run", return_value=subprocess.CompletedProcess([], 22)), \
             patch.dict(os.environ, {"GITHUB_REPOSITORY": "cerniva/ai-shared-workspace", "GITHUB_TOKEN": "test-secret-never-print"}), \
             contextlib.redirect_stderr(stderr):
            rc = main(["--run-id", "12", "--name", "shorts-free-render",
                       "--destination", str(self.root / "downloaded"), "--report", str(report)])
        self.assertEqual(rc, 3)
        self.assertNotIn("test-secret-never-print", stderr.getvalue())
        self.assertFalse(report.exists())
        self.assertFalse((self.root / "downloaded").exists())


    def test_main_success_persists_real_ledger_learning_decision(self):
        """Exercise the real ledger/catalog, simulated download, manifest and read-back."""
        report = self.root / "verified-render-artifact.json"
        destination = self.root / "downloaded"
        zip_bytes = self.zip_path.read_bytes()
        artifact = {
            "id": 23, "digest": self.digest,
            "archive_download_url": "https://api.github.com/repos/cerniva/ai-shared-workspace/actions/artifacts/23/zip",
        }

        def fake_download(argv, **kwargs):
            Path(argv[argv.index("--output") + 1]).write_bytes(zip_bytes)
            return subprocess.CompletedProcess(argv, 0)

        stdout = io.StringIO()
        with patch("scripts.verify_render_artifact.fetch_metadata", return_value=artifact), \
             patch("scripts.verify_render_artifact.subprocess.run", side_effect=fake_download), \
             patch.dict(os.environ, {"GITHUB_REPOSITORY": "cerniva/ai-shared-workspace", "GITHUB_TOKEN": "test-token"}), \
             contextlib.redirect_stdout(stdout):
            rc = main(["--run-id", "99", "--name", "shorts-free-render",
                       "--destination", str(destination), "--report", str(report)])
        self.assertEqual(rc, 0)
        decision = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(decision["status"], "PASS")
        self.assertEqual(decision["verification_scope"], "cross_run_artifact_integrity_only")
        self.assertEqual(decision["consumer"], "youtube-upload.yml:render_artifact")
        self.assertEqual(decision["run_id"], 99)
        self.assertEqual(decision["artifact_id"], 23)
        self.assertEqual(decision["artifact_digest"], self.digest)
        self.assertEqual(decision["decision_before"], "reject_unverified_cross_run_artifact")
        self.assertEqual(decision["decision_after"], "accept_digest_verified_cross_run_artifact")
        self.assertEqual(decision["applied_learning_ids"], [LEARNING_ID])
        self.assertEqual(decision["source_ids"], [SOURCE_ID])
        self.assertEqual(json.loads(stdout.getvalue()), decision)
        self.assertEqual((destination / "short.mp4").read_bytes(), b"video")

        # The nonpublishing verifier must not claim YouTube upload consumption.
        readonly_report = self.root / "readonly-verification.json"
        readonly_destination = self.root / "readonly-render"
        with patch("scripts.verify_render_artifact.fetch_metadata", return_value=artifact), \
             patch("scripts.verify_render_artifact.subprocess.run", side_effect=fake_download), \
             patch.dict(os.environ, {"GITHUB_REPOSITORY": "cerniva/ai-shared-workspace", "GITHUB_TOKEN": "test-token"}):
            rc = main(["--run-id", "99", "--name", "shorts-free-render",
                       "--destination", str(readonly_destination), "--report", str(readonly_report),
                       "--consumer", "verify-render-artifact-only.yml:read_only"])
        self.assertEqual(rc, 0)
        readonly = json.loads(readonly_report.read_text(encoding="utf-8"))
        self.assertEqual(readonly["consumer"], "verify-render-artifact-only.yml:read_only")
        self.assertEqual(readonly["applied_learning_ids"], [LEARNING_ID])
        self.assertEqual(readonly["artifact_digest"], self.digest)

    def test_main_mismatched_digest_never_writes_applied_learning_manifest(self):
        """Even with an active real learning, a bad digest cannot authorize consumption."""
        report = self.root / "verified-render-artifact.json"
        destination = self.root / "downloaded"
        zip_bytes = self.zip_path.read_bytes()
        artifact = {
            "id": 24, "digest": "sha256:" + "0" * 64,
            "archive_download_url": "https://api.github.com/repos/cerniva/ai-shared-workspace/actions/artifacts/24/zip",
        }

        def fake_download(argv, **kwargs):
            Path(argv[argv.index("--output") + 1]).write_bytes(zip_bytes)
            return subprocess.CompletedProcess(argv, 0)

        stderr = io.StringIO()
        with patch("scripts.verify_render_artifact.fetch_metadata", return_value=artifact), \
             patch("scripts.verify_render_artifact.subprocess.run", side_effect=fake_download), \
             patch.dict(os.environ, {"GITHUB_REPOSITORY": "cerniva/ai-shared-workspace", "GITHUB_TOKEN": "test-token"}), \
             contextlib.redirect_stderr(stderr):
            rc = main(["--run-id", "100", "--name", "shorts-free-render",
                       "--destination", str(destination), "--report", str(report)])
        self.assertEqual(rc, 3)
        self.assertIn("digest mismatch", stderr.getvalue())
        self.assertFalse(report.exists())
        self.assertFalse(destination.exists())


    def test_existing_report_reuse_fails_closed_before_any_consumer_action(self):
        """A stale PASS report must never be silently overwritten or reused."""
        report = self.root / "verified-render-artifact.json"
        old = '{"status":"PASS","applied_learning_ids":["stale"]}\n'
        report.write_text(old, encoding="utf-8")
        destination = self.root / "downloaded"
        stderr = io.StringIO()
        with patch("scripts.verify_render_artifact.active_rule") as learning, \
             patch("scripts.verify_render_artifact.fetch_metadata") as metadata, \
             contextlib.redirect_stderr(stderr):
            rc = main(["--run-id", "99", "--name", "shorts-free-render",
                       "--destination", str(destination), "--report", str(report)])
        self.assertEqual(rc, 3)
        self.assertIn("existing verification report", stderr.getvalue())
        self.assertEqual(report.read_text(encoding="utf-8"), old)
        self.assertFalse(destination.exists())
        learning.assert_not_called()
        metadata.assert_not_called()

    def test_missing_inactive_or_superseded_learning_blocks_full_consumer(self):
        """Reject before any remote artifact fetch, not only in the rule helper."""
        for state in ("missing", "inactive", "superseded"):
            with self.subTest(state=state):
                rows = [] if state == "missing" else [{
                    "learning_id": LEARNING_ID, "status": state,
                    "source_ids": [SOURCE_ID], "decision": "digest mismatch must fail",
                }]
                stderr = io.StringIO()
                report = self.root / "report.json"
                destination = self.root / "downloaded"
                with patch("scripts.verify_render_artifact.LearningLedger") as ledger, \
                     patch("scripts.verify_render_artifact.fetch_metadata") as metadata, \
                     contextlib.redirect_stderr(stderr):
                    ledger.return_value.for_plan.return_value = rows
                    rc = main(["--run-id", "99", "--name", "shorts-free-render",
                               "--destination", str(destination), "--report", str(report)])
                self.assertEqual(rc, 3)
                self.assertIn("learning missing or superseded", stderr.getvalue())
                self.assertFalse(report.exists())
                self.assertFalse(destination.exists())
                metadata.assert_not_called()



if __name__ == "__main__":
    unittest.main()
