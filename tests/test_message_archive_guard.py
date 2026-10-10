#!/usr/bin/env python3
"""Mesaj arşivi koruması: sahte satır (SEE_FILE, `$(cat `) CI'ı kırar; onarım mantığı test edilir."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archive_heal as h  # noqa: E402


class LiveArchiveGuard(unittest.TestCase):
    def test_no_bogus_lines_in_message_archives(self):
        for rel in h.ARCHIVES:
            text = (ROOT / rel).read_text(encoding="utf-8")
            self.assertEqual(h.bogus_lines(text), [], f"{rel}: SEE_FILE veya $(cat satırı var")


class RebuildLogic(unittest.TestCase):
    def test_bogus_overwrite_is_healed_append_only(self):
        a = "# Arşiv\n\n---\nid: A\n---\nbir\n"
        b = a + "\n---\nid: B\n---\niki\n"
        bad1 = "$(cat /tmp/x.md)"
        bad2 = "SEE_FILE\n\n---\nid: C\n---\nüç\n"
        bad3 = bad2 + "\n---\nid: D\n---\ndört\n"
        out = h.rebuild([a, b, bad1, bad2, bad3])
        self.assertTrue(out.startswith(b.rstrip("\n")))
        for token in ("id: A", "id: B", "id: C", "id: D"):
            self.assertEqual(out.count(token), 1, token)
        self.assertLess(out.index("id: C"), out.index("id: D"))
        self.assertEqual(h.bogus_lines(out), [])
        self.assertFalse(h.has_bogus_head(out))

    def test_restore_that_dropped_entries_keeps_them(self):
        a = "# Arşiv\n\n---\nid: A\n---\nbir\n\n---\nid: B\n---\niki\n"
        restore = "# Arşiv\n\n---\nid: A\n---\nbir\n\n---\nid: C\n---\nüç\n"
        out = h.rebuild([a, "PLACEHOLDER\n\n---\nid: C\n---\nüç\n", restore])
        for token in ("id: A", "id: B", "id: C"):
            self.assertEqual(out.count(token), 1, token)

    def test_check_rule(self):
        self.assertTrue(h.is_bogus_line("SEE_FILE"))
        self.assertTrue(h.is_bogus_line("$(cat /tmp/team-reports-append.md)"))
        self.assertFalse(h.is_bogus_line("Not: SEE_FILE yazmak yasak"))


if __name__ == "__main__":
    unittest.main()
