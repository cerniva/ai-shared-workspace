import os
import tempfile
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

    def test_anthropic_uses_wif_when_api_key_is_missing(self):
        response_text = '{"id":"ai-browser","steps":[]}'
        with tempfile.NamedTemporaryFile("w", delete=False) as token_file:
            token_file.write("github-oidc-jwt")
            token_path = token_file.name

        env = {
            "ANTHROPIC_API_KEY": "",
            "ANTHROPIC_MODEL": "claude-opus-5-5",
            "ANTHROPIC_FEDERATION_RULE_ID": "fdrl_test",
            "ANTHROPIC_ORGANIZATION_ID": "00000000-0000-0000-0000-000000000000",
            "ANTHROPIC_SERVICE_ACCOUNT_ID": "svac_test",
            "ANTHROPIC_WORKSPACE_ID": "wrkspc_test",
            "ANTHROPIC_IDENTITY_TOKEN_FILE": token_path,
        }
        try:
            with patch.dict(os.environ, env, clear=False), \
                 patch.object(ai_planner, "_post", side_effect=[
                     {"access_token": "sk-ant-oat01-test", "expires_in": 600},
                     {"content": [{"type": "text", "text": response_text}]},
                 ]) as post:
                task = ai_planner._anthropic("test objective")
        finally:
            os.unlink(token_path)

        self.assertEqual(task["id"], "ai-browser")
        self.assertEqual(post.call_count, 2)
        exchange = post.call_args_list[0]
        self.assertEqual(exchange.args[0], "https://api.anthropic.com/v1/oauth/token")
        self.assertEqual(exchange.args[2]["assertion"], "github-oidc-jwt")
        self.assertEqual(exchange.args[2]["federation_rule_id"], "fdrl_test")
        self.assertEqual(exchange.args[2]["service_account_id"], "svac_test")
        request = post.call_args_list[1]
        self.assertEqual(request.args[1]["Authorization"], "Bearer sk-ant-oat01-test")


if __name__ == "__main__":
    unittest.main()
