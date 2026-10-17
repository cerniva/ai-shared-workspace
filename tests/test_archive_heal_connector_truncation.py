import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_heal as ah  # noqa: E402

MARK = "[+467706 bytes at .content[1].resource.text]"


class ConnectorTruncationTests(unittest.TestCase):
    """7b08d67f: MCP get_file_contents kesik okuması arşive geri yazıldı."""

    def test_marker_line_is_bogus(self):
        self.assertTrue(ah.is_bogus_line("evidence: labels included SENT. No " + MARK))
        self.assertTrue(ah.is_bogus_line(MARK))
        self.assertEqual(ah.bogus_lines("a\nb " + MARK), [2])

    def test_real_mentions_are_kept(self):
        for line in [
            "evidence: konektör '[+N bytes at .content[1]]' ekliyor, satır ortasında bahsediliyor ve devam ediyor",
            "status: done",
        ]:
            self.assertFalse(ah.is_bogus_line(line), line)

    def test_drop_bogus_drops_truncated_line(self):
        text = "---\nid: X\n---\n\nintent: y\nevidence: labels included SENT. No " + MARK
        self.assertEqual(ah.drop_bogus(text), "---\nid: X\n---\n\nintent: y")
        self.assertEqual(ah.drop_bogus("a\n" + MARK + "\nb"), "a\nb")


if __name__ == "__main__":
    unittest.main()
