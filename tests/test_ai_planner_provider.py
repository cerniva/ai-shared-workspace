import os
import unittest
from unittest.mock import patch

from browser_worker import ai_planner


class AIPlannerProviderTests(unittest.TestCase):
    def test_explicit_anthropic_provider_skips_other_providers(self):
        anthropic_task = {"id": "ai-browser", "steps": []}

        with patch.object(ai_planner, "_anthropic", return_value=anthropic_task.copy()) as anthropic, \
             patch.object(ai_planner, "_openai") as openai, \
             patch.object(ai_planner, "_grok") as grok, \
             patch.object(ai_planner, "_gemini") as gemini:
            task = ai_planner.plan("test objective", provider="anthropic")

        self.assertEqual(task["planner_provider"], "anthropic")
        anthropic.assert_called_once_with("test objective")
        openai.assert_not_called()
        grok.assert_not_called()
        gemini.assert_not_called()

    def test_auto_provider_preserves_existing_fallback_order(self):
        final_task = {"id": "ai-browser", "steps": []}

        with patch.object(ai_planner, "_openai", side_effect=RuntimeError("openai down")) as openai, \
             patch.object(ai_planner, "_grok", side_effect=RuntimeError("grok down")) as grok, \
             patch.object(ai_planner, "_gemini", return_value=final_task.copy()) as gemini, \
             patch.object(ai_planner, "_anthropic") as anthropic:
            task = ai_planner.plan("test objective", provider="auto")

        self.assertEqual(task["planner_provider"], "gemini")
        openai.assert_called_once_with("test objective")
        grok.assert_called_once_with("test objective")
        gemini.assert_called_once_with("test objective")
        anthropic.assert_not_called()

    def test_invalid_provider_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unsupported planner provider"):
            ai_planner.plan("test objective", provider="not-a-provider")

    def test_provider_can_come_from_environment(self):
        with patch.dict(os.environ, {"BROWSER_PLANNER_PROVIDER": "anthropic"}, clear=False), \
             patch.object(ai_planner, "_anthropic", return_value={"id": "ai-browser", "steps": []}) as anthropic, \
             patch.object(ai_planner, "_openai") as openai:
            task = ai_planner.plan("test objective")

        self.assertEqual(task["planner_provider"], "anthropic")
        anthropic.assert_called_once_with("test objective")
        openai.assert_not_called()


if __name__ == "__main__":
    unittest.main()
