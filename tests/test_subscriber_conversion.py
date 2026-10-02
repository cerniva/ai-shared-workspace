import unittest

from scripts.subscriber_conversion import (
    net_subscribers_per_1000_engaged_views,
    video_subscriber_report_params,
    watch_page_net_subscribers,
)


class SubscriberConversionTests(unittest.TestCase):
    def test_net_and_rate(self):
        self.assertEqual(watch_page_net_subscribers(12, 3), 9)
        self.assertEqual(net_subscribers_per_1000_engaged_views(12, 3, 2000), 4.5)
        self.assertIsNone(net_subscribers_per_1000_engaged_views(1, 0, 0))

    def test_query_is_video_filtered_and_labeled(self):
        params = video_subscriber_report_params("KBQEvBAgp6E")
        self.assertEqual(params["filters"], "video==KBQEvBAgp6E")
        self.assertIn("subscribersGained", params["metrics"])
        self.assertEqual(params["label"], "watch-page-attributed")

    def test_rejects_filter_injection(self):
        with self.assertRaises(ValueError):
            video_subscriber_report_params("abc,video==other")


if __name__ == "__main__":
    unittest.main()
