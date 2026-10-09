# Four coding agents — controlled onboarding (NOT ACTIVE)

Scope: cerniva/ai-shared-workspace. PayoutLens is excluded. This file is an onboarding plan, not evidence that any external agent is installed, authorized, or executing.

## Agents
| Agent | Intended role | Activation gate | Current state |
|---|---|---|---|
| OpenHands | issue-driven repair PRs | Install official GitHub Action/app, review permissions and model cost, isolated branch, smoke test | NOT_CONNECTED |
| OpenAI Codex | independent implementation and regression tests | Create Codex environment for this repository; confirm authenticated access, isolated branch, smoke test | NO_ENVIRONMENT |
| GitHub Copilot coding agent | issue-to-PR implementation and review | Enable coding agent in GitHub account/repository, verify plan/billing and permissions, smoke test | NOT_VERIFIED |
| Google Jules | independent investigation and PRs | Authorize Jules GitHub app for this repository only, review data access, smoke test | NOT_CONNECTED |

## Shared operating rules
- Existing Grok/Grok bot and ChatGPT workflows remain authoritative; no replacement or automatic takeover.
- Never touch PayoutLens, secrets, credentials, payment, production settings, or unrelated projects.
- No direct main pushes by new agents; each agent works on a separate branch/PR. No automatic merges or deployments.
- Single task owner and stable task_id; no duplicate agents working the same issue without an explicit comparison request.
- Priority P0 > P1 > P2; verify live issue state and previous attempts before assigning.
- Every proposal: evidence, root cause, smallest patch, regression tests, CI SHA match, rollback and read-back.
- Changes are only DONE after verified CI/smoke/read-back; label as BLOCKED_EXTERNAL until app permissions, environment, and funding are confirmed.
- Do not put API keys in issues, PRs, logs, reports, email, or agent prompts.
- If any of the four agents changes GitHub state, the existing GitHub-to-Grok mail bridge must report task_id, SHA/PR, changed paths, reason, CI/read-back, status and Grok next_action. Do not claim delivery without Gmail message_id + thread_id.
- Onboarding must be completed one provider at a time, with a zero/low-cost smoke test and explicit verification before activation.

## Setup references (official)
- OpenHands GitHub Action: https://docs.openhands.dev/openhands/usage/run-openhands/github-action
- Codex: https://chatgpt.com/codex
- GitHub Copilot: https://github.com/features/copilot
- Jules: https://jules.google/docs/

## Next verification
1. Check account-level authorization, repository scope, available plans/quotas and billing for each provider.
2. Enable least-privilege repo access with no PayoutLens scope where separable.
3. Run a non-mutating repository-reading task first; then one isolated PR with test evidence.
4. Update statuses only from live provider/CI proof, never from this document alone.
