import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "knowledge" / "learning_ledger.json"
LEARNING_ID = "learn_4be05d4051f86fd5"
SOURCE_ID = "src_f093e461ee7afc85"


class PlaybackLocationContextGateTests(unittest.TestCase):
    def test_machine_ledger_keeps_playback_location_gate(self):
        ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
        rows = [
            row
            for row in ledger["learnings"]
            if row.get("learning_id") == LEARNING_ID
        ]
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertTrue(row["decision"].startswith("PLAYBACK_LOCATION_CONTEXT_GATE:"))
        self.assertIn("insightPlaybackLocationType", row["claim"])
        self.assertIn("insightTrafficSourceType", row["claim"])
        self.assertIn(SOURCE_ID, row["source_ids"])
        self.assertEqual(row["evidence_status"], "verified")
        self.assertIn("unknown", row["decision"])
        self.assertNotIn("PayoutLens", json.dumps(row))


if __name__ == "__main__":
    unittest.main()
