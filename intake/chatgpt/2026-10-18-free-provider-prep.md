# Free provider prep (Groq / OpenRouter) - 2026-10-18

from: chatgpt (prep only) | base: main 8fc7894e | context: RPT-20261018-0408 -> `usable: []`
No key values, tokens or account data in this file. Doc only; no code change committed.

## What the code reads (read from main 8fc7894e)

`scripts/model_fallback.py` has no hard-coded env names. `build_adapter` reads `spec["env"]` (key) and
`_model()` reads `spec["model_env"]` (override) else `spec["model"]`; both come from `config/model_providers.json`.

| provider (config name) | key secret/env | model override env | default model (code/config) | endpoint |
|---|---|---|---|---|
| `groq` | `GROQ_API_KEY` | `GROQ_MODEL` (optional) | `openai/gpt-oss-20b` | https://api.groq.com/openai/v1/chat/completions |
| `openrouter_free` | `OPENROUTER_API_KEY` | `OPENROUTER_MODEL` (optional, must end with `:free`, else default is forced) | `google/gemma-4-31b-it:free` | https://openrouter.ai/api/v1/chat/completions |
| `cerebras` (trial credit, not permanent free) | `CEREBRAS_API_KEY` | `CEREBRAS_MODEL` | `gpt-oss-120b` | https://api.cerebras.ai/v1/chat/completions |

Notes:
- `require_suffix: ":free"` on openrouter_free: an override without `:free` is ignored (never routes to a paid model).
- `fallback_models` in config (`nvidia/nemotron-3-super-120b-a12b:free`, `google/gemma-4-26b-a4b-it:free`) is NOT read by
  `model_fallback.py` (only `model`/`model_env`); it is documentation only.

## Model verification (2026-10-18)

- Groq `openai/gpt-oss-20b`: VERIFIED listed as Production model on https://console.groq.com/docs/models (also `openai/gpt-oss-120b`).
  Free-plan limits (30 RPM / 1,000 RPD / 8,000 TPM / 200,000 TPD) come from knowledge/free_llm_api_options.md (2026-10-10); UNVERIFIED today.
- OpenRouter `google/gemma-4-31b-it:free`: VERIFIED on https://openrouter.ai/google/gemma-4-31b-it:free (price Free, 262K ctx, provider Google AI Studio).
  Fallback `:free` ids above: UNVERIFIED today. Free-tier limits (50 req/day, 20 req/min without purchased credits): from knowledge file, UNVERIFIED today.

## Is a config/code change needed?

`config/model_providers.json` and `scripts/model_fallback.py`: NO change needed; adding the secret is enough for
workflows that already export it. Found exported (`KEY: ${{ secrets.KEY }}`) in: provider-health.yml, team-worker.yml,
ai-worker-gpt56.yml, improvement-bot.yml (Groq+OpenRouter only).

GAP: `.github/workflows/research-learner.yml` (the job that keeps reporting `groq=no_key` in handoff notes) exports only
GEMINI/DEEPSEEK/ANTHROPIC/OPENAI/GITHUB_TOKEN. After the secret is added it would still see `groq=no_key`.
Minimal diff (proposal, NOT committed; needs Grok/Furkan review, workflow file):

```diff
--- a/.github/workflows/research-learner.yml
+++ b/.github/workflows/research-learner.yml
@@ jobs.agent.env
       OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
       GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
+      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
+      OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
+      CEREBRAS_API_KEY: ${{ secrets.CEREBRAS_API_KEY }}
+      MISTRAL_API_KEY: ${{ secrets.MISTRAL_API_KEY }}
```

Other model-using workflows (e.g. agents-reporter, lesson-learner, telegram-bot) were not checked; check them the same way.

## Where to get the keys (official)

- Groq: https://console.groq.com/keys (sign in -> API Keys -> Create API Key). Docs: https://console.groq.com/docs/models
- OpenRouter: https://openrouter.ai/keys (sign in -> Create Key). Free models: https://openrouter.ai/models?pricing=free
- Both need Furkan's sign-in in the box browser. Do not buy credits / add payment without explicit approval.

## Steps for Grok Bot (add as GitHub repo secret)

1. Furkan signs in at the URL above in the box browser; create the key; copy it only into the secret form (never into chat, files, logs, commit messages).
2. Add the secret, either:
   - Web UI: https://github.com/cerniva/ai-shared-workspace/settings/secrets/actions -> New repository secret -> Name `GROQ_API_KEY` (or `OPENROUTER_API_KEY`) -> paste -> Add secret; or
   - CLI: `gh secret set GROQ_API_KEY --repo cerniva/ai-shared-workspace` (prompts for the value; do not pass it as an argument or echo it).
3. Verify by name only: `gh secret list --repo cerniva/ai-shared-workspace` shows `GROQ_API_KEY` / `OPENROUTER_API_KEY`.
4. Run provider-health (workflow_dispatch if available, else next schedule) and read back `state/provider_health.json` on main:
   expect `groq` / `openrouter_free` status `ok` and listed under `usable`.
5. If research-learner must use it, apply the env diff above via a reviewed branch, then re-check its next run.
6. Report with an RPT entry: secret NAMES only, run id, provider_health result.

constraints: PayoutLens and grok-chatgpt-masa untouched. No secrets written. No PR/merge.
