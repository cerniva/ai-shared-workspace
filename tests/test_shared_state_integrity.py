import json
import tempfile
import unittest
from pathlib import Path

from scripts.shared_state_integrity import (
    IntegrityError,
    check_handoffs,
    check_message,
    check_repo,
)

ROOT = Path(__file__).resolve().parents[1]


class SharedStateIntegrityTests(unittest.TestCase):
    def test_repository_shared_state_is_valid(self):
        self.assertGreaterEqual(check_repo(ROOT), 1)

    def test_reject_shell_substitution_replacing_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoffs.json"
            path.write_text("$(cat /tmp/handoffs.json)", encoding="utf-8")
            with self.assertRaises(IntegrityError):
                check_handoffs(path)

    def test_reject_valid_json_wrong_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoffs.json"
            path.write_text(json.dumps("not a ledger"), encoding="utf-8")
            with self.assertRaises(IntegrityError):
                check_handoffs(path)

    def test_reject_placeholder_replacing_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "grok-to-chatgpt.md"
            path.write_text("FULL_CONTENT_" + "PLACE" + "HOLDER", encoding="utf-8")
            with self.assertRaises(IntegrityError):
                check_message(path, "# Grok → ChatGPT")

    def test_reject_truncated_archive_with_original_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "grok-to-chatgpt.md"
            path.write_text("# Grok → ChatGPT\\n\\n---\\nid: MSG-1\\n", encoding="utf-8")
            with self.assertRaises(IntegrityError):
                check_message(path, "# Grok → ChatGPT", 300000)

    def test_reject_missing_or_empty_archive(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "team-reports.md"
            with self.assertRaises(IntegrityError):
                check_message(path, "# Ortak ekip raporları")
            path.write_text("# Ortak ekip raporları\n", encoding="utf-8")
            with self.assertRaises(IntegrityError):
                check_message(path, "# Ortak ekip raporları")


if __name__ == "__main__":
    unittest.main()
