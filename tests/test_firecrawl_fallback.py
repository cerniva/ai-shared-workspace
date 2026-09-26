import unittest
import urllib.error
from unittest.mock import patch

from scripts import shared_web_worker as t


class FirecrawlFallbackTests(unittest.TestCase):
    def test_retryable_tinyfish_fetch_falls_back_to_firecrawl(self):
        task = {"id": "F-FALLBACK", "requested_by": "chatgpt", "mode": "fetch", "urls": ["https://example.com"]}
        err = urllib.error.HTTPError("u", 503, "busy", {}, None)
        with patch.object(t.tiny, "fetch", side_effect=err), patch.object(t, "firecrawl_fetch", return_value={"pages": [{"url": "https://example.com", "markdown": "ok"}]}) as fallback:
            status, data, reason = t.execute_task(task, "tiny-key", ledger={})
        self.assertEqual(status, "done")
        self.assertEqual(reason, "")
        self.assertEqual(data["provider"], "firecrawl")
        fallback.assert_called_once_with(["https://example.com"])

    def test_permission_error_does_not_bypass_to_firecrawl(self):
        task = {"id": "F-AUTH", "requested_by": "chatgpt", "mode": "fetch", "urls": ["https://example.com"]}
        err = urllib.error.HTTPError("u", 401, "bad key", {}, None)
        with patch.object(t.tiny, "fetch", side_effect=err), patch.object(t, "firecrawl_fetch") as fallback:
            status, data, _ = t.execute_task(task, "tiny-key", ledger={})
        self.assertEqual(status, "blocked")
        self.assertEqual(data["reason_code"], "api-permission")
        fallback.assert_not_called()

    def test_retryable_tinyfish_browser_falls_back_to_firecrawl(self):
        task = {"id": "B-FALLBACK", "requested_by": "grok", "mode": "browser", "url": "https://example.com", "goal": "Open pricing and report plans"}
        err = urllib.error.HTTPError("u", 503, "busy", {}, None)
        with patch.object(t.tiny, "run_browser", side_effect=err), patch.object(t, "firecrawl_browser", return_value={"output": "plans"}) as fallback:
            status, data, reason = t.execute_task(task, "tiny-key", ledger={})
        self.assertEqual(status, "done")
        self.assertEqual(reason, "")
        self.assertEqual(data["provider"], "firecrawl")
        fallback.assert_called_once_with("https://example.com", "Open pricing and report plans")

    def test_prohibited_browser_goal_is_never_sent_to_fallback(self):
        task = {"id": "B-BLOCK", "requested_by": "chatgpt", "mode": "browser", "url": "https://example.com", "goal": "login and pay"}
        self.assertTrue(t.browser_block_reason(task))
        with patch.object(t, "firecrawl_browser") as fallback:
            with self.assertRaises(ValueError):
                t.build_firecrawl_browser_request(task)
        fallback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
