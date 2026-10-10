import io
import json
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from scripts import tinyfish_youtube as ty

ROOT = Path(__file__).resolve().parents[1]
OAUTH = {"YOUTUBE_CLIENT_ID": "x", "YOUTUBE_CLIENT_SECRET": "y", "YOUTUBE_REFRESH_TOKEN": "z"}


class FakeResp:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return json.dumps(self.body).encode()


class TinyfishYoutubeTests(unittest.TestCase):
    def call(self, argv, env, opener=None):
        out = io.StringIO()
        with redirect_stdout(out):
            code = ty.main(argv, env=env, opener=opener or self.fail_opener)
        return code, json.loads(out.getvalue())

    def fail_opener(self, *a, **k):
        raise AssertionError("network must not be called")

    def test_analytics_payload_is_read_only_and_uses_profile(self):
        p = ty.analytics_payload(env={ty.PROFILE_ENV: "prof_1"})
        self.assertTrue(p["use_profile"])
        self.assertEqual(p["profile_id"], "prof_1")
        self.assertIn("READ ONLY", p["goal"])
        self.assertIn("Do not upload", p["goal"])
        self.assertNotIn("profile_id", ty.analytics_payload(env={}, config=Path("/nonexistent.json")))

    def test_profile_falls_back_to_repo_config(self):
        self.assertEqual(ty.analytics_payload(env={})["profile_id"], "prof_2ef79634882f4d6b")
        self.assertEqual(ty.profile_id_for("google_signed_in", env={}), "prof_996c5c04908047c5")
        self.assertEqual(ty.profile_id_for("youtube_studio", env={ty.PROFILE_ENV: "prof_env"}), "prof_env")

    def test_analytics_workflow_is_manual_and_read_only(self):
        text = (ROOT / ".github" / "workflows" / "tinyfish-youtube-analytics.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", text)
        # weekly learning loop: scheduled, commits only knowledge/shorts/learnings
        self.assertIn("schedule", text)
        self.assertIn("git add knowledge/shorts/learnings", text)
        self.assertNotIn("youtube_upload.py", text)
        self.assertIn("python3 scripts/tinyfish_youtube.py analytics --execute", text)
        self.assertIn("secrets.TINYFISH_API_KEY", text)
        self.assertIn("upload-artifact", text)

    def test_senses_allowlist_includes_youtube(self):
        from scripts import tinyfish_senses
        for host in ("studio.youtube.com", "www.youtube.com", "youtube.com"):
            self.assertIn(host, tinyfish_senses.ALLOWED_HOSTS)

    def test_dry_run_is_default_and_offline(self):
        code, out = self.call(["analytics"], {"TINYFISH_API_KEY": "k"})
        self.assertEqual(code, 0)
        self.assertTrue(out["dry_run"])
        self.assertNotIn("k", json.dumps(out["payload"]).split('"goal"')[0])

    def test_execute_without_key_is_blocked(self):
        code, out = self.call(["analytics", "--execute"], {})
        self.assertEqual(code, 2)
        self.assertEqual(out["reason_code"], "missing-secret")

    def test_execute_sends_key_header_only(self):
        seen = {}

        def opener(req, timeout):
            seen["key"] = req.get_header("X-api-key")
            seen["body"] = req.data.decode()
            return FakeResp({"run_id": "r1", "status": "COMPLETED", "result": {"views": 5}})

        code, out = self.call(["analytics", "--execute"], {"TINYFISH_API_KEY": "secret-k"}, opener)
        self.assertEqual(code, 0)
        self.assertEqual(seen["key"], "secret-k")
        self.assertNotIn("secret-k", seen["body"])
        self.assertEqual(out["result"], {"views": 5})

    def test_http_error_is_reported_not_raised(self):
        import urllib.error

        def opener(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 401, "Unauthorized", {}, io.BytesIO(b'{"code":"INVALID_API_KEY"}'))

        code, out = self.call(["analytics", "--execute"], {"TINYFISH_API_KEY": "k"}, opener)
        self.assertEqual(code, 1)
        self.assertEqual(out["http_status"], 401)
        self.assertIn("INVALID_API_KEY", out["detail"])

    def test_upload_route(self):
        self.assertEqual(ty.upload_route(OAUTH)["route"], "youtube_api")
        blocked = ty.upload_route({})
        self.assertEqual(blocked["route"], "blocked")
        self.assertEqual(blocked["missing"], list(ty.YOUTUBE_OAUTH_ENV))
        self.assertEqual(ty.upload_route(OAUTH, privacy="public")["route"], "blocked")
        code, out = self.call(["upload-route"], {})
        self.assertEqual(code, 3)
        self.assertEqual(out["privacy"], "private")


if __name__ == "__main__":
    unittest.main()
