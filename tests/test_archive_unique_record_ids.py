import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_heal as ah  # noqa: E402


class UniqueRecordIdTests(unittest.TestCase):
    def test_unique_ids_pass(self):
        text = "id: A\nbody\n## RPT-1\nx\nid: B\n## RPT-2\n"
        ah.assert_unique_record_ids(text, "t.md")

    def test_duplicate_message_id_fails(self):
        text = "id: A\nfoo\nid: A\n"
        with self.assertRaises(SystemExit) as cm:
            ah.assert_unique_record_ids(text, "t.md")
        self.assertIn("duplicate record IDs", str(cm.exception))
        self.assertIn("A", str(cm.exception))

    def test_duplicate_report_id_fails(self):
        text = "## RPT-1\nx\n## RPT-1\n"
        with self.assertRaises(SystemExit) as cm:
            ah.assert_unique_record_ids(text, "t.md")
        self.assertIn("duplicate record IDs", str(cm.exception))
        self.assertIn("RPT-1", str(cm.exception))

    def test_live_archives_have_unique_ids(self):
        root = Path(__file__).resolve().parents[1]
        for rel in ah.ARCHIVES:
            f = root / rel
            if f.exists():
                ah.assert_unique_record_ids(f.read_text(encoding="utf-8"), rel)


if __name__ == "__main__":
    unittest.main()
