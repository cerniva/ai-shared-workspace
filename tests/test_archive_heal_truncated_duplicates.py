"""Regression: archive-heal 2026-10-17 kırmızısı (truncated duplicate records)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_heal as h  # noqa: E402


FULL = (
    "id: MSG-1\nfrom: grok\nstatus: seen\n---\n\nintent: GÖRDÜM\nevidence: tam kayıt\n"
)


class TruncatedDuplicateTests(unittest.TestCase):
    def test_header_only_copy_of_message_is_dropped(self):
        text = FULL + "\n\n" + "id: MSG-1\nfrom: grok\nstatus: seen\n\n---\nid: MSG-2\nfrom: grok\n---\nbody2\n"
        out = h.drop_truncated_duplicate_records(text)
        self.assertEqual(out.count("id: MSG-1"), 1)
        self.assertIn("id: MSG-2", out)
        self.assertIn("evidence: tam kayıt", out)
        h.assert_unique_record_ids(out, "x")

    def test_real_conflicting_duplicate_still_fails_closed(self):
        text = FULL + "\n---\nid: MSG-1\nfrom: grok\nstatus: seen\n---\nfarklı içerik\n"
        out = h.drop_truncated_duplicate_records(text)
        with self.assertRaises(SystemExit):
            h.assert_unique_record_ids(out, "x")

    def test_repeated_rpt_section_without_metadata_is_dropped(self):
        rpt = "## RPT-1\n\n- Kanıt: a\n- Karar: b\n"
        text = "---\nid: RPT-1\nfrom: grok\n---\n\n" + rpt + "\n---\n\n" + rpt + "\n---\nid: RPT-2\n---\n\n## RPT-2\n\n- c\n"
        out = h.drop_truncated_duplicate_records(text)
        self.assertEqual(out.count("## RPT-1"), 1)
        self.assertIn("## RPT-2", out)
        h.assert_unique_record_ids(out, "x")

    def test_metadata_heading_pair_is_one_record(self):
        text = "---\nid: RPT-9\n---\n\n## RPT-9\n\n- a\n"
        self.assertEqual(h.drop_truncated_duplicate_records(text), text)
        h.assert_unique_record_ids(text, "x")

    def test_full_content_placeholder_line_is_bogus(self):
        line = "[full content from /tmp/team-reports.md would be here, including the new report section]"
        self.assertTrue(h.is_bogus_line(line))
        self.assertFalse(h.is_bogus_line("- Not: [full content] kelimesi geçen gerçek satır değil mi? evet"))


if __name__ == "__main__":
    unittest.main()
