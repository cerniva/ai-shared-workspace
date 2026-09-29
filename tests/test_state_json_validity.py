from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CORE_STATE_FILES = (
    "state/now.json",
    "state/cross_chat_sync.json",
    "state/worker_health.json",
)


class CoreStateJsonValidityTests(unittest.TestCase):
    def test_core_state_files_are_valid_json_objects(self) -> None:
        for relative in CORE_STATE_FILES:
            with self.subTest(path=relative):
                value = json.loads((ROOT / relative).read_text(encoding="utf-8"))
                self.assertIsInstance(value, dict)


if __name__ == "__main__":
    unittest.main()
