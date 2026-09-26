import unittest

from browser_worker.policy import (
    PolicyViolation, enforce_action, normalize_allow_hosts, safe_url,
)


class BrowserPolicyTests(unittest.TestCase):
    def setUp(self):
        self.hosts = normalize_allow_hosts("example.com, shop.example.org")

    def test_exact_and_subdomain_allowed(self):
        self.assertEqual(safe_url("https://example.com/path", self.hosts), "https://example.com/path")
        self.assertEqual(safe_url("https://www.example.com", self.hosts), "https://www.example.com")

    def test_foreign_host_blocked(self):
        with self.assertRaisesRegex(PolicyViolation, "outside allowlist"):
            safe_url("https://evil-example.com", self.hosts)

    def test_non_http_and_embedded_credentials_blocked(self):
        for url in ("file:///etc/passwd", "javascript:alert(1)", "https://user:pass@example.com"):
            with self.subTest(url=url), self.assertRaises(PolicyViolation):
                safe_url(url, self.hosts)

    def test_private_addresses_and_local_names_blocked(self):
        for url in ("http://127.0.0.1", "http://10.0.0.8", "http://localhost"):
            with self.subTest(url=url), self.assertRaises(PolicyViolation):
                safe_url(url, self.hosts)

    def test_read_only_is_default(self):
        for action in ("click", "fill", "press"):
            with self.subTest(action=action), self.assertRaisesRegex(PolicyViolation, "approval_required"):
                enforce_action(action, "read_only", "Search")

    def test_interactive_blocks_secrets_and_high_impact_targets(self):
        with self.assertRaisesRegex(PolicyViolation, "sensitive fields"):
            enforce_action("fill", "interactive", "Email", {"type": "password"})
        with self.assertRaisesRegex(PolicyViolation, "high-impact"):
            enforce_action("click", "interactive", "Publish now")

    def test_interactive_allows_named_low_impact_control(self):
        enforce_action("click", "interactive", "Open menu")

    def test_allowlist_rejects_url_syntax_and_empty_value(self):
        for value in ("", "https://example.com", "example.com/path"):
            with self.subTest(value=value), self.assertRaises(PolicyViolation):
                normalize_allow_hosts(value)


if __name__ == "__main__":
    unittest.main()
