"""Regression coverage for source-duration bounds in a rights-neutral Shorts preflight."""
import unittest

from scripts.shorts_multisegment_preflight import build_concat_graph, validate_segments


class SourceBoundsTests(unittest.TestCase):
    def test_outside_source_less_than_one_millisecond_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "beyond source duration"):
            validate_segments([(0, 35.0005)], 35)

    def test_segment_starting_beyond_source_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "beyond source duration"):
            validate_segments([(0, 30), (35.0001, 35.0008)], 35)

    def test_end_exactly_on_source_is_allowed(self):
        self.assertEqual(validate_segments([(0, 35)], 35), 35.0)

    def test_nomiku_cut_still_passes(self):
        self.assertEqual(validate_segments([(0, 15.4), (58, 79.1)], 84.49), 36.5)

    def test_graph_contains_both_original_audio_cuts(self):
        graph = build_concat_graph([(0, 15.4), (58, 79.1)], 84.49)
        self.assertIn("atrim=start=58.000:end=79.100", graph)
        self.assertIn("concat=n=2:v=1:a=1", graph)


if __name__ == "__main__":
    unittest.main()
