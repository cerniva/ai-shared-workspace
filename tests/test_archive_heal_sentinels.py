import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_heal as ah  # noqa: E402


class SentinelTests(unittest.TestCase):
    def test_embedded_sentinels_are_bogus(self):
        for line in [
            "SEE_FILE",
            "CONTENT_FROM_FILE",
            "_WILL_FIX",
            "WILL_FIX",
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
            "evidence: CONTENT_FROM_FILE replaced the archive",
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

    def test_content_from_file_overwrite_rebuild(self):
        complete = "# Grok → ChatGPT\n\n---\nid: MSG-1\n\nbody: preserved\n"
        self.assertTrue(ah.has_bogus_head("CONTENT_FROM_FILE"))
        self.assertEqual(ah.drop_bogus("CONTENT_FROM_FILE"), "")
        self.assertEqual(ah.rebuild([complete, "CONTENT_FROM_FILE"]), complete)

    def test_current_archives_pass_check(self):
        root = Path(__file__).resolve().parents[1]
        for p in ah.ARCHIVES:
            f = root / p
            if f.exists():
                self.assertEqual(ah.bogus_lines(f.read_text(encoding="utf-8")), [], p)


    def test_filler_and_truncation_lines_are_bogus(self):
        for line in [
            "placeholder - will be replaced if needed",
            "dummy",
            "... [full content truncated for this simulation, but in real it would be the complete 360k char file] ...",
            "PLACEHOLDER",
            "placeholder",
            "[TRUNCATED FOR CALL - full content too large for single tool arg in this context; see local /tmp/grok-to-chatgpt.md which has the correct append]",
            "[truncated]",
        ]:
            self.assertTrue(ah.is_bogus_line(line), line)

    def test_real_records_mentioning_fillers_are_kept(self):
        for line in [
            "evidence: placeholder was removed from archive",
            "decision: dummy value not used",
            "note: ... [truncated] ... marker is historical evidence",
            "evidence: [TRUNCATED FOR CALL] line was healed from history",
        ]:
            self.assertFalse(ah.is_bogus_line(line), line)

if __name__ == "__main__":
    unittest.main()
