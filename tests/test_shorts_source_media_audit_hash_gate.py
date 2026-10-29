"""Regression tests for fail-closed downloaded source SHA audit (not rights approval)."""
from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/shorts-source-media-audit.yml"


class SourceMediaAuditHashGateTests(unittest.TestCase):
    def test_workflow_compares_downloaded_media_to_pinned_candidate_sha(self):
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("nasa_nutrition_33p8s_rights_pending.json", workflow)
        self.assertIn('["source_sha256"]', workflow)
        self.assertIn("sha256sum --check audit/source.expected.sha256", workflow)
        self.assertIn("SOURCE_HASH_MISMATCH", workflow)

    @unittest.skipUnless(shutil.which("sha256sum"), "sha256sum not installed")
    def test_expected_sha_check_rejects_tampered_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.webm"
            expected = root / "source.expected.sha256"
            source.write_bytes(b"original source bytes")
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            expected.write_text(f"{digest}  source.webm\\n", encoding="ascii")
            good = subprocess.run(
                ["sha256sum", "--check", expected.name],
                cwd=root, capture_output=True, text=True, check=False,
            )
            self.assertEqual(good.returncode, 0, good.stderr)
            source.write_bytes(b"modified source bytes")
            bad = subprocess.run(
                ["sha256sum", "--check", expected.name],
                cwd=root, capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn("FAILED", bad.stdout)


if __name__ == "__main__":
    unittest.main()
