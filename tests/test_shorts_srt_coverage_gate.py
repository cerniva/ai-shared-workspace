import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.shorts_srt_timeline import audit, read_cues

class TimelineGapRegression(unittest.TestCase):
    def test_large_gap_must_not_pass_preflight(self):
        text = ('1\n00:00:00,000 --> 00:00:02,000\nHello\n\n'
                '2\n00:00:29,000 --> 00:00:32,000\nWorld\n')
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'srt.srt'
            path.write_text(text, encoding='utf-8')
            report = audit(path, hashlib.sha256(path.read_bytes()).hexdigest(), [(0, 32)])
            self.assertEqual(report['technical_preflight_gate'], 'BLOCKED')
            self.assertIn('CAPTION_TIMELINE_GAP_REVIEW', report['technical_preflight_blockers'])
            self.assertEqual(report['caption_timeline_uncovered_gaps'], [[2.0, 29.0]])
            self.assertFalse(report['publish_ready'])

    def test_full_coverage_still_passes_technical_only(self):
        text = '1\n00:00:00,000 --> 00:00:32,000\nHello\n'
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'srt.srt'
            path.write_text(text, encoding='utf-8')
            report = audit(path, hashlib.sha256(path.read_bytes()).hexdigest(), [(0, 32)])
            self.assertEqual(report['technical_preflight_gate'], 'PASS_TECHNICAL_ONLY')
            self.assertEqual(report['caption_timeline_uncovered_gaps'], [])
            self.assertFalse(report['publish_ready'])

    def test_markup_only_caption_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'missing visible cue text'):
            read_cues('1\n00:00:00,000 --> 00:00:32,000\n<i></i>\n')

if __name__ == '__main__':
    unittest.main()
