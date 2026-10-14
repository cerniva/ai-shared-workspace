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

    def test_every_message_record_has_archive_separator(self):
        for rel in h.ARCHIVES:
            lines = (ROOT / rel).read_text(encoding="utf-8").splitlines()
            missing = [
                line_no
                for line_no, line in enumerate(lines)
                if line.startswith("id:") and line_no > 0 and lines[line_no - 1].strip() != "---"
            ]
            self.assertEqual(missing, [], f"{rel}: kayıt ayıracı eksik, satırlar={missing[:5]}")


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


class TruncationArtifactRule(unittest.TestCase):
    """2026-10-12: Grok'un LLM yanit metni arsive sizdi
    ('[... full content truncated in this example ...]'); guard bunu kaciriyordu."""

    def test_leaked_llm_answer_line_is_bogus(self):
        leaked = ("[... full content truncated in this example for the response, "
                  "but in real it would be the full 368k from /tmp/grok-to-chatgpt.md ...]")
        self.assertTrue(h.is_bogus_line(leaked))
        self.assertTrue(h.is_bogus_line("[... truncated ...]"))
        self.assertTrue(h.is_bogus_line("[ ... content truncated ... ]."))

    def test_real_evidence_line_mentioning_truncation_is_not_bogus(self):
        self.assertFalse(h.is_bogus_line(
            "- evidence: GÖRDÜM commit abc. Mail body truncated in the notice."))
        self.assertFalse(h.is_bogus_line("decision_or_conflict: the next-task sentence is truncated."))

    def test_drop_bogus_keeps_every_record_id(self):
        archive = "# Arşiv\n\n---\nid: A\n---\nbir\n\n[... truncated ...]\n\n---\nid: B\n---\niki\n"
        out = h.drop_bogus(archive)
        self.assertEqual(h.bogus_lines(out), [])
        for token in ("id: A", "id: B"):
            self.assertEqual(out.count(token), 1, token)


if __name__ == "__main__":
    unittest.main()
