import os
import unittest
from unittest.mock import patch

from engine_router import choose_engine


class EngineRouterTests(unittest.TestCase):
    def test_playwright_is_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(choose_engine({}), "playwright")

    def test_explicit_skyvern_requires_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "SKYVERN_API_KEY"):
                choose_engine({"engine": "skyvern"})

    def test_explicit_skyvern_allowed_with_key(self):
        with patch.dict(os.environ, {"SKYVERN_API_KEY": "test"}, clear=True):
            self.assertEqual(choose_engine({"engine": "skyvern"}), "skyvern")

    def test_unknown_engine_is_rejected(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, "unsupported browser engine"):
                choose_engine({"engine": "other"})


if __name__ == "__main__":
    unittest.main()
