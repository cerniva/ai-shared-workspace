import unittest

from shorts_worker.worker import ShortsWorker


class ShortsWorkerTests(unittest.TestCase):
    def test_draft_uses_research_result(self):
        worker = ShortsWorker(youtube_api_available=True)
        result = worker.draft(topic="bitcoin pizza", research_provider="exa")
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.metadata["topic"], "bitcoin pizza")
        self.assertEqual(result.metadata["research_provider"], "exa")

    def test_analytics_prefers_youtube_api(self):
        worker = ShortsWorker(youtube_api_available=True)
        result = worker.analytics(video_id="abc123")
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.provider, "youtube_api")

    def test_analytics_fail_closed_when_api_missing(self):
        worker = ShortsWorker(youtube_api_available=False)
        result = worker.analytics(video_id="abc123")
        self.assertEqual(result.status, "blocked")
        self.assertIsNone(result.provider)

    def test_publish_requires_explicit_approval(self):
        worker = ShortsWorker(youtube_api_available=True)
        result = worker.publish(video_path="video.mp4", approved=False)
        self.assertEqual(result.status, "approval_required")
        self.assertIsNone(result.provider)

    def test_approved_publish_routes_to_youtube_api(self):
        worker = ShortsWorker(youtube_api_available=True)
        result = worker.publish(video_path="video.mp4", approved=True)
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.provider, "youtube_api")


if __name__ == "__main__":
    unittest.main()
