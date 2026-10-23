import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.verify_render_artifact import LEARNING_ID, SOURCE_ID, active_rule, verify_and_extract


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


if __name__ == "__main__":
    unittest.main()
