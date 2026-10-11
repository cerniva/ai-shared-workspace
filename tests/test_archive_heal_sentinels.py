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


    def test_exact_orphan_markers_and_casefold(self):
        markers = [
            "placeholder - will be replaced if needed",
            "dummy",
            "... [full content truncated for this simulation, but in real it would be the complete 360k char file] ...",
            "_FIXED_BY_FULL_CONTENT",
        ]
        for marker in markers:
            with self.subTest(marker=marker):
                self.assertTrue(ah.is_bogus_line(marker))
                self.assertTrue(ah.is_bogus_line("  " + marker + "  "))
                self.assertTrue(ah.has_bogus_head(marker + "\\n## real"))
                self.assertEqual(ah.strip_head(marker + "\\n## real"), "## real")

    def test_orphan_markers_are_removed_without_losing_records(self):
        markers = [
            "placeholder - will be replaced if needed",
            "dummy",
            "... [full content truncated for this simulation, but in real it would be the complete 360k char file] ...",
            "_FIXED_BY_FULL_CONTENT",
        ]
        real = [
            "id: MSG-20261010-0001-test",
            "evidence: the word dummy was quoted in a real report",
            "id: MSG-20261010-0002-test",
            "note: _FIXED_BY_FULL_CONTENT appears inside a valid record",
        ]
        sample = "\\n".join([real[0], markers[0], real[1], markers[1], real[2],
                            markers[2], real[3], markers[3]]) + "\\n"
        self.assertEqual(ah.bogus_lines(sample), [2, 4, 6, 8])
        self.assertEqual(ah.drop_bogus(sample), "\\n".join(real) + "\\n")

    def test_ordinary_mentions_are_not_orphan_markers(self):
        for line in [
            "evidence: placeholder - will be replaced if needed was found",
            "- Grok reported dummy as an orphan marker",
            "note: ... [full content truncated for this simulation, but in real it would be the complete 360k char file] ...",
            "report: _FIXED_BY_FULL_CONTENT",
        ]:
            self.assertFalse(ah.is_bogus_line(line), line)

    def test_current_archives_pass_check(self):
        root = Path(__file__).resolve().parents[1]
        for p in ah.ARCHIVES:
            f = root / p
            if f.exists():
                self.assertEqual(ah.bogus_lines(f.read_text(encoding="utf-8")), [], p)


if __name__ == "__main__":
    unittest.main()
