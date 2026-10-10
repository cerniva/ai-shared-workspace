"""Regresyon: scripts/ sys.path'te olsa bile knowledge_bridge tek kez yüklenmeli.

shorts-render-tests run 38011995250 (55146758): bir test scripts/ dizinini sys.path'e
ekleyince scripts.learning_bridge/knowledge_promote/knowledge_freshness bare
`knowledge_bridge` modülünü ikinci kez yükledi; iki ayrı CatalogError sınıfı oluştu ve
fail-closed testlerinde assertRaises eşleşmedi (28 failed).
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROBE = r"""
import sys
sys.path.insert(0, {scripts!r})
sys.path.insert(0, {root!r})
import scripts.learning_bridge as lb
import scripts.knowledge_promote as kp
import scripts.knowledge_freshness as kf
import scripts.knowledge_bridge as kb
assert "knowledge_bridge" not in sys.modules, "bare knowledge_bridge yüklendi"
assert lb.CatalogError is kb.CatalogError
assert kp.CatalogError is kb.CatalogError
assert kf.CatalogError is kb.CatalogError
print("OK")
"""


class KnowledgeImportIdentityTests(unittest.TestCase):
    def test_package_import_does_not_load_bare_knowledge_bridge(self):
        code = PROBE.format(scripts=str(ROOT / "scripts"), root=str(ROOT))
        proc = subprocess.run(
            [sys.executable, "-c", code], cwd=str(ROOT), capture_output=True, text=True, timeout=60
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("OK", proc.stdout)


if __name__ == "__main__":
    unittest.main()
