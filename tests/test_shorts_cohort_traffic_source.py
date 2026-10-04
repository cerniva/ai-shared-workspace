import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from shorts_cohort_traffic_source import classify_cohort_traffic


class CohortTrafficTests(unittest.TestCase):
    def test_missing_source_is_unknown(self):
        result = classify_cohort_traffic({"views": 1000, "creatorContentType": "SHORTS"})
        self.assertEqual(result["status"], "unknown")
        self.assertIsNone(result["source_type"])

    def test_shorts_swipe_has_no_detail(self):
        ok = classify_cohort_traffic({"insightTrafficSourceType": "SHORTS"})
        self.assertEqual(ok["status"], "accept")
        self.assertFalse(ok["detail_applicable"])
        bad = classify_cohort_traffic({
            "insightTrafficSourceType": "SHORTS",
            "insightTrafficSourceDetail": "previous-video",
        })
        self.assertEqual(bad["status"], "reject")

    def test_search_detail_is_term_not_cause(self):
        result = classify_cohort_traffic({
            "insightTrafficSourceType": "YT_SEARCH",
            "insightTrafficSourceDetail": "desk lamp",
            "creatorContentType": "SHORTS",
        })
        self.assertEqual(result["status"], "accept")
        self.assertEqual(result["detail_meaning"], "search_term")
        self.assertFalse(result["causal"])
        self.assertIn("not the traffic source", result["note"])

    def test_sound_page_is_not_swipe(self):
        result = classify_cohort_traffic({"insightTrafficSourceType": "SOUND_PAGE"})
        self.assertEqual(result["status"], "accept")
        self.assertIn("not the vertical-swipe", result["reason"])

    def test_undocumented_detail_rejected(self):
        result = classify_cohort_traffic({
            "insightTrafficSourceType": "HASHTAGS",
            "insightTrafficSourceDetail": "invented",
        })
        self.assertEqual(result["status"], "reject")


if __name__ == "__main__":
    unittest.main()
