"""Regression tests for millisecond-serialized FFmpeg cut duration gates."""
import unittest

from scripts.shorts_multisegment_preflight import build_concat_graph, validate_segments


class SerializedDurationGateTests(unittest.TestCase):
    def test_exact_30_second_edit_not_rejected_by_binary_float_error(self):
        # Raw Python float arithmetic gives 29.999999999999993.
        cuts = [(0, 15.4), (58, 72.6)]
        self.assertEqual(validate_segments(cuts, 84.49), 30.0)
        graph = build_concat_graph(cuts, 84.49)
        self.assertIn("atrim=start=58.000:end=72.600", graph)

    def test_under_30_seconds_after_serialization_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "30–40 seconds"):
            validate_segments([(0, 29.9994)], 35)

    def test_serialized_end_beyond_source_is_rejected(self):
        # 84.4885 is inside source 84.4886, but FFmpeg emits end=84.489.
        with self.assertRaisesRegex(ValueError, "serialized segment extends"):
            validate_segments([(0, 15), (60, 84.4885)], 84.4886)

    def test_nomiku_36p5_second_plan_is_unchanged(self):
        self.assertEqual(validate_segments([(0, 15.4), (58, 79.1)], 84.49), 36.5)


if __name__ == "__main__":
    unittest.main()
