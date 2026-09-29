import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class Core05SharedStateJsonTests(unittest.TestCase):
    def test_core05_shared_state_files_are_valid_json_objects(self):
        for rel in ("state/now.json", "state/cross_chat_sync.json", "state/worker_health.json"):
            with self.subTest(path=rel):
                data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
                self.assertIsInstance(data, dict)

if __name__ == "__main__":
    unittest.main()
