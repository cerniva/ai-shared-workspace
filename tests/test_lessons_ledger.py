"""knowledge/lessons.md integrity (required check `test` via knowledge-lint)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "knowledge" / "lessons.md"
HEADER_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}|Rules|Strategies)$")


class LessonsLedgerTests(unittest.TestCase):
    def setUp(self):
        self.text = LEDGER.read_text(encoding="utf-8")
        self.lines = self.text.splitlines()

    def test_no_merge_conflict_markers(self):
        bad = [i + 1 for i, l in enumerate(self.lines) if re.match(r"^(<{7}|={7}|>{7})( |$)", l)]
        self.assertEqual(bad, [], f"conflict markers at lines {bad}")

    def test_section_headers(self):
        bad = [l for l in self.lines if l.startswith("## ") and not HEADER_RE.match(l)]
        self.assertEqual(bad, [])

    def test_no_duplicate_entries_or_slugs(self):
        entries = [l for l in self.lines if l.startswith("- ") and " | " in l]
        self.assertGreater(len(entries), 0)
        self.assertEqual(len(entries), len(set(entries)), "duplicate ledger line")
        slugs = [e[2:].split(" | ", 1)[0].strip() for e in entries]
        dups = sorted({s for s in slugs if slugs.count(s) > 1})
        self.assertEqual(dups, [], f"duplicate slugs: {dups}")

    def test_no_shell_paste_artifacts(self):
        for l in self.lines:
            self.assertNotRegex(l, r"^\$\(cat |^SEE_FILE\b|^PLACEHOLDER\b")


if __name__ == "__main__":
    unittest.main()
