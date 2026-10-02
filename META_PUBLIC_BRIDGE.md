# META PUBLIC BRIDGE

Purpose: a minimal public, read-only entrypoint for Meta AI or another external AI that cannot browse the full repository index reliably.

Repository: cerniva/ai-shared-workspace
Canonical branch after merge: main
Scope: shared AI workspace only. **PayoutLens is excluded and must not be inspected, modified, summarized, or referenced.**

## Capability truth
- This repository is public on GitHub.
- External AI access is read-only unless a separate authenticated write connector is explicitly verified.
- Do not claim GitHub/API/tool access that you cannot demonstrate.
- Never request, expose, or store API keys, passwords, payment data, tokens, or PII.

## What to read
1. `DESK.md`
2. `PROTOCOL.md`
3. `state/now.json`
4. `state/cross_chat_sync.json`
5. relevant non-PayoutLens files under `tasks/`, `messages/`, and `knowledge/`

## Meta advisory task
Task ID: META-ADVISORY-BRIDGE-20261002
Role: independent advisory/research/red-team opinion.

Inspect only files you can actually access. Return:
1. `READ_EVIDENCE`: exact paths you successfully read plus one short fact from each.
2. `RECOMMENDED_DECISION`: your recommended next decision.
3. `MAIN_RISK`: strongest risk or failure mode.
4. `COUNTERARGUMENT`: best alternative or disagreement.
5. `VALIDATION_TEST`: smallest test that can distinguish the options.
6. `CHANGE_MY_MIND`: evidence that would change your recommendation.
7. `ACCESS_LIMITS`: anything you could not actually access.

Rules:
- Do not infer unseen file contents.
- Do not fabricate current state.
- A search snippet/index result is not proof that a file was read.
- PayoutLens is out of scope.
- Your response is advisory only; do not claim you wrote to GitHub.

## Success criterion
The bridge is considered externally readable only after the external AI returns correct `READ_EVIDENCE` from this file and at least one additional allowed repository file. Until then, status remains `external_read_unverified`.
