"""Regression: archive-heal 39026188674/39026232613 (2026-10-17 13:47 TRT) kırmızısı.

b93549b grok-to-chatgpt.md'yi '[... truncated for this example ...]' ile 34 satıra indirdi.
rebuild() penceredeki eski bir sürümden başladığı için 1f0dbc8'de geri eklenen
MSG-20261014-0125 `---` ayracını kaybetti ve heal 'missing record delimiter' ile durdu.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import archive_heal as h  # noqa: E402

PATH = "messages/heal-delimiter-fixture.md"  # gerçek arşiv yolu apply_notes notlarını ekler
HEAD = "# Grok → ChatGPT\n\n"
R1 = "---\nid: MSG-1\nfrom: grok\n---\n\nbody one\n"
# Eski sürüm daha uzun (fazla boş satır) olduğu için heal onu taban alıyor (gerçek durum).
R2_NO_DELIM = "\n\n\n\n\n\n\nid: MSG-2\nfrom: grok\n---\n\nbody two\n"
R2 = "\n---\nid: MSG-2\nfrom: grok\n---\n\nbody two\n"
R3 = "\n---\nid: MSG-3\nfrom: grok\n---\n\nbody three\n"
BAD = "[... truncated for this example, but in reality full content would be here ...]"


class RestoreDelimiterTests(unittest.TestCase):
    def test_restores_delimiter_seen_in_history(self):
        broken = HEAD + R1 + R2_NO_DELIM
        fixed = HEAD + R1 + R2
        out = h.restore_known_delimiters(broken, [broken, fixed])
        self.assertEqual(h.missing_record_delimiters(out), [])
        self.assertEqual(out.count("id: MSG-2"), 1)

    def test_unknown_missing_delimiter_stays_fail_closed(self):
        broken = HEAD + R1 + R2_NO_DELIM
        out = h.restore_known_delimiters(broken, [broken])
        self.assertNotEqual(h.missing_record_delimiters(out), [])

    def test_noop_when_clean(self):
        clean = HEAD + R1 + R2
        self.assertEqual(h.restore_known_delimiters(clean, [clean]), clean)

    def test_heal_old_window_start_truncated_head(self):
        v_old = HEAD + R1 + R2_NO_DELIM
        v_bad_old = HEAD + "SEE_FILE\n"
        v_fixed = HEAD + R1 + R2
        head = HEAD + R1.split("\n")[0] + "\n" + BAD + "\n" + R3
        versions = [v_old, v_bad_old, v_fixed, head]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "messages").mkdir()
            (root / PATH).write_text(head, encoding="utf-8")
            old_root, old_hist = h.ROOT, h.history
            h.ROOT, h.history = root, (lambda p, s: list(versions))
            try:
                rep = h.heal(PATH, "14 days ago", True)
            finally:
                h.ROOT, h.history = old_root, old_hist
            out = (root / PATH).read_text(encoding="utf-8")
        self.assertTrue(rep["damaged"])
        self.assertEqual(h.missing_record_delimiters(out), [])
        self.assertNotIn(BAD, out)
        for rid in ("MSG-1", "MSG-2", "MSG-3"):
            self.assertEqual(out.count(f"id: {rid}\n"), 1, rid)

    def test_heal_without_restore_was_fail_closed(self):
        orig = h.restore_known_delimiters
        h.restore_known_delimiters = lambda r, v: r
        try:
            with self.assertRaises(ValueError):
                self.test_heal_old_window_start_truncated_head()
        finally:
            h.restore_known_delimiters = orig


if __name__ == "__main__":
    unittest.main()
