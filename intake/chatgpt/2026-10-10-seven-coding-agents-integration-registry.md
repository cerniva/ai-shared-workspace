# Coding agents integration registry — 2026-10-10
status: prepared_unconnected
owner: ChatGPT / Grok coordination
scope: cerniva/ai-shared-workspace ONLY
protected: PayoutLens (never read/edit/modify)
policy: No agent may publish, pay, deploy, merge, delete, or access production credentials without Furkan's separate approval.

## Evaluated tools and routing
| Agent | Role | Integration | State | Next proof |
|---|---|---|---|---|
| Cursor Cloud Agents | primary autonomous repo debugging/testing, phone-first | https://cursor.com/agents GitHub app, isolated branch | not_connected | GitHub authorization, small PR, CI pass |
| Claude Code | code review, refactoring, CI tests | https://github.com/apps/claude + https://github.com/anthropics/claude-code-action ; auth in GitHub secrets | not_connected | approved installation, test PR |
| Devin | complex multi-step engineering | https://devin.ai/ GitHub integration (verify account, permissions, pricing) | not_connected | sandbox issue->PR evidence |
| Replit Agent | isolated prototypes and runnable tests | https://replit.com/ GitHub import | not_connected | import into separate sandbox, test log |
| Bolt.new | frontend/prototype | https://bolt.new/ GitHub import/two-way sync | not_connected | separate branch/project demo |
| Lovable | frontend dashboard/prototype | https://lovable.dev/ GitHub integration; do not assume existing repo can import directly | not_connected | isolated project with export/PR |
| GitHub Copilot coding agent | GitHub issue to PR; distinguish from legacy Copilot Workspace product | https://github.com/features/copilot | not_connected | eligible plan/agent assignment and CI proof |

## Guardrails
1. Keep GitHub as canonical coordination source; read PROTOCOL.md, DESK.md, state/, tasks/, messages/, knowledge/ before code edits.
2. One task owner at a time; claim in state/handoffs, short append-only reports, canonical dedup; agent runs in its own branch.
3. Never give all-repositories access if selected-repository permission is available; exclude PayoutLens, production secrets, personal data and billing.
4. Allow read/search/branch/test/PR only; main protected; merge, deploy, publishing, OAuth approvals, payments and irreversible actions require Furkan's explicit authorization.
5. Real proof: commit SHA, changed paths, test command/output, CI URL, read-back on branch, PR review; otherwise mark blocked/unverified.
6. Prefer existing credits/free plans; do not start paid trials or background agents with unverified costs; track quotas and stop at cap.
7. Security: prompt-injection-resistant browsing, least privilege, no secrets in issue/comment/chat/repo, no unattended write to protected resources.
8. Integrate incrementally: Cursor or GitHub Copilot first, Claude Code second, Devin optional; Replit/Bolt/Lovable in separate app sandboxes to avoid conflicting changes.
9. No workflow, installation, subscription or integration is claimed active by this registry; accounts and OAuth require user action.

## First safe smoke task
Read one existing non-PayoutLens Python test, reproduce a failure or identify a real edge case, make the smallest fix in a new branch, run targeted test and CI, submit PR. Do not merge. Report blocked if access/cost unavailable.

## Source docs
- https://cursor.com/docs/agent/overview
- https://docs.cursor.com/en/background-agent/web-and-mobile
- https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md
- https://bolt.new/blog/github-hackathon
- https://docs.replit.com/replit-workspace/workspace-features/version-control

## Manual authorizations required
Each provider needs account sign-in and GitHub repo permission from Furkan. Claude may require API/OAuth secret and billing; do not invent or request secret values in chat. Cursor Cloud Agents may incur usage costs. Replit/Lovable/Bolt may create distinct app repos rather than safely ingest the monorepo; verify first.
