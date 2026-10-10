"""Catalog exceptions stay catchable when scripts is also on sys.path."""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class BridgeImportIdentityTests(unittest.TestCase):
    def test_script_path_does_not_create_second_catalog_error(self):
        code = """
import sys
sys.path.insert(0, 'scripts')
from scripts.knowledge_bridge import CatalogError
from scripts import learning_bridge, knowledge_promote, knowledge_freshness
assert learning_bridge.CatalogError is CatalogError
assert knowledge_promote.CatalogError is CatalogError
assert knowledge_freshness.CatalogError is CatalogError
"""
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bridge_clis_start_from_outside_repo(self):
        for name in ("learning_bridge.py", "knowledge_promote.py", "knowledge_freshness.py"):
            with self.subTest(script=name):
                result = subprocess.run([sys.executable, str(ROOT / "scripts" / name), "--help"],
                                        cwd=ROOT.parent, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
