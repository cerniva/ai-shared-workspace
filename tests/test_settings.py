import unittest

from runtime.settings import Settings


class SettingsTests(unittest.TestCase):
    def test_defaults_and_ready_flag(self):
        s = Settings.from_env({"GITHUB_TOKEN": "tok"})
        self.assertTrue(s.ready_for_github)
        self.assertEqual(s.github_repo, "cerniva/ai-shared-workspace")
        self.assertEqual(s.github_branch, "private-replit-runtime-v1")
        self.assertEqual(s.poll_seconds, 60)
        self.assertEqual(s.runtime_id, "replit-runtime-v1")

    def test_expected_branch_can_be_set_without_exposing_token(self):
        s = Settings.from_env({
            "GITHUB_TOKEN": "SECRET",
            "GITHUB_BRANCH": "private-replit-runtime-v1",
        })
        self.assertTrue(s.ready_for_github)
        self.assertEqual(s.github_branch, "private-replit-runtime-v1")
        self.assertNotIn("SECRET", repr(s))

    def test_wrong_repo_fails_closed(self):
        s = Settings.from_env({
            "GITHUB_TOKEN": "SECRET",
            "GITHUB_REPO": "cerniva/other-repo",
            "GITHUB_BRANCH": "private-replit-runtime-v1",
        })
        self.assertFalse(s.ready_for_github)

    def test_wrong_branch_fails_closed(self):
        s = Settings.from_env({
            "GITHUB_TOKEN": "SECRET",
            "GITHUB_REPO": "cerniva/ai-shared-workspace",
            "GITHUB_BRANCH": "main",
        })
        self.assertFalse(s.ready_for_github)

    def test_missing_token_is_safe(self):
        s = Settings.from_env({})
        self.assertFalse(s.ready_for_github)
        self.assertNotIn("tok", repr(s).lower())

    def test_invalid_poll_fails_closed_to_sixty(self):
        for value in ("nope", "0", "-5"):
            self.assertEqual(Settings.from_env({"POLL_SECONDS": value}).poll_seconds, 60)


if __name__ == "__main__":
    unittest.main()
