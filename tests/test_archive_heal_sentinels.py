import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_heal as ah  # noqa: E402


class SentinelTests(unittest.TestCase):
    def test_embedded_sentinels_are_bogus(self):
        for line in [
            "SEE_FILE",
            "$(cat /tmp/x.md)",
            "FULL_CONTENT_WILL_BE_REPLACED",
            "  FULL_CONTENT_WILL_BE_REPLACED  ",
            "THE_FULL_CONTENT_HERE_IS_TOO_LARGE_TO_PASTE...",
            "THE_FULL_CONTENT_HERE_IS_TOO_LARGE_TO_PASTE_SO_I_WILL_APPEND",
            "THE_CONTENT_FROM_TMP_FILE",
            "PLACEHOLDER",
        ]:
            self.assertTrue(ah.is_bogus_line(line), line)

    def test_mentions_inside_real_records_are_kept(self):
        for line in [
            "evidence: live main still had FULL_CONTENT_WILL_BE_REPLACED, THE_CONTENT_FROM_TMP_FILE",
            "- completed: üç sahte satır (THE_FULL_CONTENT_HERE_IS_TOO_LARGE_TO_PASTE) silindi",
            "## RPT-20261010-1451",
            "---",
            "",
        ]:
            self.assertFalse(ah.is_bogus_line(line), line)

    def test_bogus_lines_reports_line_numbers(self):
        text = "## A\nreal\nFULL_CONTENT_WILL_BE_REPLACED\nmore\nTHE_CONTENT_FROM_TMP_FILE\n"
        self.assertEqual(ah.bogus_lines(text), [3, 5])

    def test_drop_bogus_keeps_real_lines(self):
        text = "## A\nreal FULL_CONTENT_WILL_BE_REPLACED mention\nFULL_CONTENT_WILL_BE_REPLACED\n\n## B\nok\n"
        self.assertEqual(ah.drop_bogus(text), "## A\nreal FULL_CONTENT_WILL_BE_REPLACED mention\n\n## B\nok\n")

    def test_current_archives_pass_check(self):
        root = Path(__file__).resolve().parents[1]
        for p in ah.ARCHIVES:
            f = root / p
            if f.exists():
                self.assertEqual(ah.bogus_lines(f.read_text(encoding="utf-8")), [], p)


if __name__ == "__main__":
    unittest.main()
