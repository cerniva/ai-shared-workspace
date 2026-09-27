import base64
import json
import unittest

from runtime.github_client import GitHubAuthError, GitHubConflict, GitHubContentsClient, GitHubNotFound
from runtime.settings import Settings


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, headers, body=None):
        self.calls.append((method, url, headers, body))
        status, payload = self.responses.pop(0)
        return status, {}, json.dumps(payload).encode()


class GitHubClientTests(unittest.TestCase):
    def settings(self):
        return Settings.from_env({"GITHUB_TOKEN": "SECRET", "GITHUB_REPO": "cerniva/ai-shared-workspace"})

    def test_get_and_put_json(self):
        encoded = base64.b64encode(json.dumps({"version": 1}).encode()).decode()
        transport = FakeTransport([(200, {"content": encoded, "sha": "old"}), (200, {"content": {"sha": "new"}})])
        c = GitHubContentsClient(self.settings(), transport=transport)
        data, sha = c.get_json("state/runtime-status.json")
        self.assertEqual(data, {"version": 1})
        self.assertEqual(sha, "old")
        self.assertEqual(c.put_json("state/runtime-status.json", data, sha, "update"), "new")
        self.assertTrue(all("cerniva/ai-shared-workspace" in call[1] for call in transport.calls))

    def test_rejects_arbitrary_url_path(self):
        c = GitHubContentsClient(self.settings(), transport=FakeTransport([]))
        with self.assertRaises(ValueError):
            c.get_json("https://evil.example/data")

    def test_safe_http_errors(self):
        for status, exc in ((401, GitHubAuthError), (403, GitHubAuthError), (404, GitHubNotFound), (409, GitHubConflict), (422, GitHubConflict)):
            c = GitHubContentsClient(self.settings(), transport=FakeTransport([(status, {"message": "SECRET"})]))
            with self.assertRaises(exc) as ctx:
                if status in (409, 422):
                    c.put_json("state/runtime-status.json", {"version": 1}, "old", "m")
                else:
                    c.get_json("state/runtime-status.json")
            self.assertNotIn("SECRET", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
