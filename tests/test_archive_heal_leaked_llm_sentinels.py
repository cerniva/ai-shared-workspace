import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_heal as ah  # noqa: E402


class LeakedLlmSentinelTests(unittest.TestCase):
    """2026-10-17: grok-to-chatgpt.md içinde guard'ın kaçırdığı üç sahte satır (PR #197/#201)."""

    def test_leaked_lines_are_bogus(self):
        for line in [
            "RESTORED_FROM_PREVIOUS_COMMIT_892adbc60d88696c8e908249186677da2f6da441",
            "test content for size check",
            "[... full previous content omitted for brevity in this call construction, but in actual would be full ...]",
        ]:
            self.assertTrue(ah.is_bogus_line(line), line)

    def test_real_mentions_are_kept(self):
        for line in [
            "evidence: RESTORED_FROM_PREVIOUS_COMMIT_abc satırı silindi",
            "- test content for size check satırı arşivden temizlendi",
        ]:
            self.assertFalse(ah.is_bogus_line(line), line)


if __name__ == "__main__":
    unittest.main()
