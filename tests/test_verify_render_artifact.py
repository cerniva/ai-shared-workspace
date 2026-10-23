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


if __name__ == "__main__":
    unittest.main()
