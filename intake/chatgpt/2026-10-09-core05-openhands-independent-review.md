# CORE-05 OpenHands Issue #111 — independent red-team, 2026-10-09

Issue #111 fetched through GitHub connector: open; research_done/integration_not_tested; no comments at inspection.

## Official references
- Agent Canvas overview: https://docs.openhands.dev/openhands/usage/agent-canvas/overview — Node.js 24+, npm, model access; direct local backend has host filesystem access, Docker isolates mounted paths.
- September 2026 release: https://hub.openhands.dev/blog/new-in-agent-canvas-september-2026 — agent profiles constrain tools/secrets, Docker isolation, Issue-to-PR and PR review improvements.
- Official repo README: https://github.com/OpenHands/OpenHands/blob/main/README.md — self-host, Docker and local paths, agent backend.
- Agent Canvas product: https://www.openhands.dev/product/canvas — OSS install; self-managed machine still needed.
- Migration FAQ: https://github.com/OpenHands/docs/issues/657 — headless/ACP modes remain supported; old headless not inherently deprecated, but unattended approval is inappropriate for this pilot.

## Independent findings / corrections
1. Do not equate install-free or API-key-free with model-free. Ollama/LM Studio require an accessible local model server and adequate resources. ACP subscription login is not guaranteed for unattended CI.
2. 'Issue-to-PR' exists, but GitHub integration permissions and exact minimum scopes depend on the selected authentication method and automation. Do not claim the Issue #111 proposed scopes are independently validated least privilege until tested against a pinned version. Initial PR-1 must use no token beyond default read-only GITHUB_TOKEN.
3. Agent Canvas local npm backend may access host files; use isolated Docker with a dedicated workspace for any later live agent. Avoid mounting parent folder containing PayoutLens, home directory, or secrets.
4. Repo-level main protection absent according to Issue #111; workflow permissions alone cannot stop a separately provisioned PAT. PR-1 policy tests should reject workflow-level/job-level write permissions, push/schedule triggers, unpinned external actions, network/model calls and non-allowlisted paths. PR-2 needs actual GitHub branch protection/ruleset or enforced token boundary, not prompt-only rules.
5. Policy tests must not claim a main branch write is impossible based only on text grep. Test an isolated negative fixture and check effective GitHub permission/config before enabling any agent.

## Minimal PR-1 scope
Only docs/OPENHANDS_INTEGRATION.md + tests/test_openhands_policy.py, no agent install, no API/LLM, no OAuth, no workflow edits, no secret. Test fixture should assert main push disallowed, PayoutLens paths disallowed, no write token, no auto-merge, and scope of future pilot limited to a single allowlisted issue. Optional workflow_dispatch-only read-only preflight belongs to follow-up PR-1b after offline tests pass.

Acceptance: stdlib offline tests PASS + git diff --check + branch SHA + PR review; no live OpenHands claim. PR-2 separately approved after real isolation, backend, scoped GitHub permission and model-cost checks. If unavailable: BLOCKED_EXTERNAL, no false green.

No OpenHands install, PR or CI run performed in this review.
