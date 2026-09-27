import unittest

from runtime.redaction import redact_text, sanitize_object


class RedactionTests(unittest.TestCase):
    def test_redacts_exact_secret_headers_and_cookies(self):
        text = "Authorization: Bearer abc123\nCookie: sid=xyz\nsecret=supersecret"
        out = redact_text(text, ["supersecret"])
        self.assertNotIn("abc123", out)
        self.assertNotIn("sid=xyz", out)
        self.assertNotIn("supersecret", out)
        self.assertIn("[REDACTED]", out)

    def test_nested_object_is_sanitized(self):
        value = {"a": ["safe", "Bearer token123"], "b": {"c": "supersecret"}}
        out = sanitize_object(value, ["supersecret"])
        self.assertEqual(out["a"][0], "safe")
        self.assertNotIn("token123", out["a"][1])
        self.assertEqual(out["b"]["c"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
